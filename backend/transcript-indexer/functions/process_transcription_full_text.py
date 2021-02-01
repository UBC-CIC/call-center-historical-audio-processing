from __future__ import print_function  # Python 2/3 compatibility

import boto3
import botocore
import os
import logging
import time
import json
from urllib.request import urlopen
import string
import random
from common_lib import find_duplicate_person, id_generator

# Logging configurations
logging.basicConfig()
logger = logging.getLogger()
if os.getenv('LOG_LEVEL') == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Environment Parameters
REGION = os.getenv('AWS_REGION', default='us-east-1')
# Pull the bucket name from the environment variable set in the cloudformation stack
BUCKET = os.environ['BUCKET_NAME']
print("bucket: " + BUCKET)

# Global Parameters
commonDict = {'i': 'I'}
ENTITY_CONFIDENCE_THRESHOLD = 0.5
KEY_PHRASES_CONFIDENCE_THRESHOLD = 0.5

# Get the necessary AWS tools
s3_client = boto3.client("s3")
comprehend_client = boto3.client(service_name='comprehend', region_name=REGION)
# transcribe_client = boto3.client('transcribe', region_name=REGION)


class InvalidInputError(ValueError):
    pass


def process_transcript(transcription_url, vocabulary_info):
    """
    Processes the transcript and returns the S3 bucket URI of processed transcript
    :param transcription_url:
    :param vocabulary_info:
    :return:
    """
    # TODO check how to add custom vocabulary here
    custom_vocabs = None

    response = urlopen(transcription_url)
    output = response.read()
    json_data = json.loads(output)

    logger.debug(json.dumps(json_data, indent=4))
    results = json_data['results']
    # free up memory
    del json_data

    comprehend_chunks, paragraphs = chunk_up_transcript(custom_vocabs, results)

    start = time.time()
    # If comprehend_chunks has > 25 chunks, batch_detect_entities errors may be thrown
    # Or if an individual document is > 5000 bytes
    detected_entities_response = comprehend_client.batch_detect_entities(TextList=comprehend_chunks, LanguageCode='en')
    round_trip = time.time() - start
    logger.info('End of batch_detect_entities. Took time {:10.4f}\n'.format(round_trip))

    entities = parse_detected_entities_response(detected_entities_response, {})
    entities_as_list = {}
    for entity_type in entities:
        entities_as_list[entity_type] = list(entities[entity_type])

    clean_up_entity_results(entities_as_list)
    print(json.dumps(entities_as_list, indent=4))

    start = time.time()
    detected_phrase_response = comprehend_client.batch_detect_key_phrases(TextList=comprehend_chunks, LanguageCode='en')
    round_trip = time.time() - start
    logger.info('End of batch_detect_key_phrases. Took time {:10.4f}\n'.format(round_trip))

    key_phrases = parse_detected_key_phrases_response(detected_phrase_response)
    logger.debug(json.dumps(key_phrases, indent=4))

    doc_to_update = {'transcript': paragraphs}
    doc_to_update['transcript_entities'] = entities_as_list
    logger.info(json.dumps(doc_to_update, indent=4))
    doc_to_update['key_phrases'] = key_phrases
    key = f'calls/transcript/{id_generator()}.json'

    response = s3_client.put_object(Body=json.dumps(doc_to_update, indent=2), Bucket=BUCKET, Key=key)
    logger.info(json.dumps(response, indent=2))

    logger.info("successfully written transcript to s3://" + BUCKET + "/" + key)
    logger.info(f"successfully written transcript to s3://{BUCKET}/{key}")
    # Return the bucket and key of the transcription / comprehend result.
    transcript_location = {"bucket": BUCKET, "key": key}
    return transcript_location


def chunk_up_transcript(custom_vocabs, results):
    """
    Takes the result from Amazon Transcribe, breaks it down into two lists with chunks of text, one with
    speaker labels (paragraphs) and one without (comprehend_chunks). The resulting text is updated with both a
    custom vocabulary that is passed in and a global vocabulary that exists as a global parameter

    :param custom_vocabs: Custom vocabulary mapping Transcribe response to an arbitrary string depending on use case
    :param results: the JSON response from Amazon Transcribe
    :return: comprehend_chunks: A list of 4500+ word chunks to be sent to Amazon Comprehend for interpretation
             paragraphs: A list of Transcribe text broken down into small chunks and separated by speaker labels
    """
    # Here is the JSON format returned by the Amazon Transcription SDK
    # Entire output examples can be found here
    # https://github.com/kibaffo33/aws_transcribe_to_docx/tree/master/sample_material
    # {
    #  "jobName": JOB_NAME,
    #  "accountId": YOUR_AWS_ACCOUNT_ID,
    #  "results":{
    #    "transcripts":[
    #        {
    #            "transcript": FULL_OUTPUT_OF_AUDIO_TRANSCRIPTION
    #        }
    #    ],
    #     "speaker_labels": {
    #       "speakers": NUMBER_OF_DETECTED_SPEAKERS_IN_AUDIO_SAMPLE,
    #       "segments": [
    #       The transcript is broken into segments, which are usually sentences
    #       This is a list of those segments
    #         {
    #           "start_time": START_TIME_FOR_THIS_SEGMENT,
    #           "speaker_label": SPEAKER_LABEL_FOR_SEGMENT,
    #           "end_time": END_TIME_FOR_THIS_SEGMENT,
    #           "items": [
    #           Each segment is further broken down into units
    #           within the segment, such as words
    #           The items list contains all segment units for that segment
    #             {
    #               "start_time": START_TIME_FOR_SEGMENT_UNIT,
    #               "speaker_label": SPEAKER_LABEL_FOR_SEGMENT_UNIT,
    #               "end_time": END_TIME_FOR_SEGMENT_UNIT
    #             },
    #             {
    #               ANOTHER_SEGMENT_UNIT
    #             },
    #             ...
    #       ]
    #     },
    #    "items":[
    #           This items list contains all the segment units of the entire transcript in order
    #           with the segment unit type (e.g word/punctuation)
    #           Segment units that are punctuation do not have start_time and end_time keys as that is inferred
    #           from the meaning of the sentence, and not the audio itself
    #        {
    #         "start_time": START_TIME_FOR_SEGMENT_UNIT,
    #         "end_time": END_TIME_FOR_SEGMENT_UNIT,
    #         "alternatives": [
    #           A list of possible predictions
    #           {
    #             "confidence": CONFIDENCE_LEVEL,
    #             "content": TRANSCRIBED_PREDICTED_TEXT
    #           }
    #         ],
    #         "type": e.g PRONUNCIATION/PUNCTUATION
    #        },
    #        {
    #          ANOTHER_SEGMENT_UNIT
    #        },
    #        ...
    #    ],
    #  },
    #  "status": JOB_STATUS
    # }
    #
    # Cropped transcribe response example
    # {
    #     "jobName": "03-speaker-identification",
    #     "accountId": "XXXXXXXXXXXX",
    #     "results": {
    #         "transcripts": [
    #             {
    #                 "transcript": "She was gone [...] she fell."
    #             }
    #         ],
    #         "speaker_labels": {
    #             "speakers": 3,
    #             "segments": [
    #                 {
    #                 "start_time": "0.49",
    #                 "speaker_label": "spk_0",
    #                 "end_time": "7.2",
    #                 "items": [
    #                     {
    #                         "start_time": "0.49",
    #                         "speaker_label": "spk_0",
    #                         "end_time": "0.7"
    #                     },
    #                     {
    #                         "start_time": "0.7",
    #                         "speaker_label": "spk_0",
    #                         "end_time": "0.86"
    #                     },
    #                     ...
    #                     {
    #                         "start_time": "6.64",
    #                         "speaker_label": "spk_0",
    #                         "end_time": "6.78"
    #                     },
    #                     {
    #                         "start_time": "6.78",
    #                         "speaker_label": "spk_0",
    #                         "end_time": "7.2"
    #                     }
    #                 ]
    #             }
    #             ]
    #         },
    #         "items": [
    #             {
    #                 "start_time": "0.49",
    #                 "end_time": "0.7",
    #                 "alternatives": [
    #                     {
    #                         "confidence": "1.0",
    #                         "content": "She"
    #                     }
    #                 ],
    #                 "type": "pronunciation"
    #             },
    #             {
    #                 "start_time": "0.7",
    #                 "end_time": "0.86",
    #                 "alternatives": [
    #                     {
    #                         "confidence": "1.0",
    #                         "content": "was"
    #                     }
    #                 ],
    #                 "type": "pronunciation"
    #             },
    #             ...
    #             {
    #                 "start_time": "6.64",
    #                 "end_time": "6.78",
    #                 "alternatives": [
    #                     {
    #                         "confidence": "1.0",
    #                         "content": "she"
    #                     }
    #                 ],
    #                 "type": "pronunciation"
    #             },
    #             {
    #                 "start_time": "6.78",
    #                 "end_time": "7.2",
    #                 "alternatives": [
    #                     {
    #                         "confidence": "1.0",
    #                         "content": "fell"
    #                     }
    #                 ],
    #                 "type": "pronunciation"
    #             },
    #             {
    #                 "alternatives": [
    #                     {
    #                         "confidence": "0.0",
    #                         "content": "."
    #                     }
    #                 ],
    #                 "type": "punctuation"
    #             }
    #         ]
    #     },
    #     "status": "COMPLETED"
    # }

    speaker_label_exist = False
    speaker_segments = None
    # If the transcription has speaker labels, parse the individual segments of speech into a list
    if 'speaker_labels' in results:
        speaker_label_exist = True
        speaker_segments = parse_speaker_segments(results)

    transcribed_units = results['items']
    last_speaker = None
    paragraphs = []
    current_paragraph = ""
    comprehend_chunks = []
    current_comprehend_chunk = ""
    previous_item_end_time = 0
    current_speaker_start_time = 0
    last_item_was_sentence_end = False
    for item in transcribed_units:
        # If the item is a word, parse, replace with vocabulary if applicable and chunk it up
        if item["type"] == "pronunciation":
            current_item_start_time = float(item['start_time'])

            # If the speaker has changed, append the aggregated transcribed words so far,
            # reset current_paragraph with the name of the new speaker, and note the time when speaker changed
            if speaker_label_exist:
                current_speaker = get_speaker_label(speaker_segments, float(item['start_time']))
                if last_speaker is None or current_speaker != last_speaker:
                    if current_paragraph is not None:
                        paragraphs.append(current_paragraph)
                    current_paragraph = f"{current_speaker} :"
                    current_speaker_start_time = current_item_start_time
                last_speaker = current_speaker

            # Else, if it has been 2 seconds since the last item, or this speaker has been speaking for 15 seconds and
            #                                                         ended a sentence
            # Add the aggregate result to paragraphs and reset current_paragraph
            elif (current_item_start_time - previous_item_end_time) > 2 or (
                    (current_item_start_time - current_speaker_start_time) > 15 and last_item_was_sentence_end):
                current_speaker_start_time = current_item_start_time
                if current_paragraph is not None or current_paragraph != "":
                    paragraphs.append(current_paragraph)
                current_paragraph = ""

            # Get the transcribed item, replace content with custom and global vocabulary,
            # then add it to the current_paragraph
            phrase = item['alternatives'][0]['content']
            if custom_vocabs is not None:
                if phrase in custom_vocabs:
                    phrase = custom_vocabs[phrase]
                    logger.info("replaced custom vocab: " + phrase)
            if phrase in commonDict:
                phrase = commonDict[phrase]
            current_paragraph = f"{current_paragraph} {phrase}"

            # Aggregate the transcribed items in chunks for Amazon Comprehend
            # This excludes speaker labels
            current_comprehend_chunk = f"{current_comprehend_chunk} {phrase}"

            last_item_was_sentence_end = False

        # Else if the item is punctuation, mark the reach of the end of a sentence
        elif item["type"] == "punctuation":
            current_paragraph = f"{current_paragraph}{item['alternatives'][0]['content']}"
            current_comprehend_chunk = f"{current_comprehend_chunk}{item['alternatives'][0]['content']}"
            if item['alternatives'][0]['content'] in (".", "!", "?"):
                last_item_was_sentence_end = True
            else:
                last_item_was_sentence_end = False

        # If we reach the end of a paragraph >= 4500 words or a paragraph > 4900 words
        # Add it to the comprehend_chunks to be sent to Amazon Comprehend
        if (item["type"] == "punctuation" and len(current_comprehend_chunk) >= 4500) \
                or len(current_comprehend_chunk) > 4900:
            comprehend_chunks.append(current_comprehend_chunk)
            current_comprehend_chunk = ""

        # Always mark item end times
        if 'end_time' in item:
            previous_item_end_time = float(item['end_time'])

    # Make sure at the end of the loop, all the aggregate result is added
    if not current_comprehend_chunk == "":
        comprehend_chunks.append(current_comprehend_chunk)
    if not current_paragraph == "":
        paragraphs.append(current_paragraph)

    logger.debug(json.dumps(paragraphs, indent=4))
    logger.debug(json.dumps(comprehend_chunks, indent=4))

    return comprehend_chunks, "\n\n".join(paragraphs)


def parse_detected_key_phrases_response(detected_phrase_response):
    """
    Given the result of batch_detect_phrases from Amazon Comprehend
    It logs the Errorlist,
    returns a list of key_phrases that are above KEY_PHRASES_CONFIDENCE_THRESHOLD, a global variable
    with no duplicate entries

    :param detected_phrase_response: Response from Amazon Comprehend for batch_detect_key_phrases
    :return: a list of noun key_phrases with no duplicates
    """
    if 'ErrorList' in detected_phrase_response and len(detected_phrase_response['ErrorList']) > 0:
        logger.error("encountered error during batch_detect_key_phrases")
        logger.error(json.dumps(detected_phrase_response['ErrorList'], indent=4))

    if 'ResultList' in detected_phrase_response:
        result_list = detected_phrase_response["ResultList"]
        phrases_set = set()
        for result in result_list:
            phrases = result['KeyPhrases']
            for detected_phrase in phrases:
                if float(detected_phrase["Score"]) >= KEY_PHRASES_CONFIDENCE_THRESHOLD:
                    phrase = detected_phrase["Text"]
                    phrases_set.add(phrase)
        key_phrases = list(phrases_set)
        return key_phrases
    else:
        return []


def clean_up_entity_results(dict_of_entity_lists):
    """
    Parses the dict of entity lists by removing duplicates from the PEOPLE entity list
    and combining commercial items and titles into the same 'products and titles' category
    """
    if 'PERSON' in dict_of_entity_lists:
        try:
            people = dict_of_entity_lists['PERSON']
            duplicates = find_duplicate_person(people)
            for d in duplicates:
                people.remove(d)
            dict_of_entity_lists['PERSON'] = people
        except Exception as e:
            logger.error(e)
    if 'COMMERCIAL_ITEM' in dict_of_entity_lists:
        dict_of_entity_lists['Products_and_Titles'] = dict_of_entity_lists['COMMERCIAL_ITEM']
        del dict_of_entity_lists['COMMERCIAL_ITEM']
    if 'TITLE' in dict_of_entity_lists:
        if 'Products_and_Titles' in dict_of_entity_lists:
            dict_of_entity_lists['Products_and_Titles'].append(dict_of_entity_lists['TITLE'])
        else:
            dict_of_entity_lists['Products_and_Titles'] = dict_of_entity_lists['TITLE']
        del dict_of_entity_lists['TITLE']


def parse_detected_entities_response(detected_entities_response, entities):
    """
    Takes the output of Amazon Comprehend batch_detect_entities and parses it
    It logs the ErrorList, and filters the ResultList by only keeping entities above
    the ENTITY_CONFIDENCE_THRESHOLD and entities that are not of type QUANTITY
    It capitalises the text for entities of type LOCATION, PERSON or ORGANIZATION

    :param detected_entities_response: Response JSON from Amazon Comprehend batch_detect_entities()
    :param entities: a dict of entities that the filtered results are added to
    :return: a dict of entity sets for each type of entity kept (e.g LOCATION, PERSON etc)
    """
    if 'ErrorList' in detected_entities_response and len(detected_entities_response['ErrorList']) > 0:
        logger.error("encountered error during batch_detect_entities")
        logger.error("error:" + json.dumps(detected_entities_response['ErrorList'], indent=4))

    if 'ResultList' in detected_entities_response:
        result_list = detected_entities_response["ResultList"]
        for result in result_list:
            detected_entities = result["Entities"]
            for detected_entity in detected_entities:
                if float(detected_entity["Score"]) >= ENTITY_CONFIDENCE_THRESHOLD:

                    entity_type = detected_entity["Type"]

                    if entity_type != 'QUANTITY':
                        text = detected_entity["Text"]

                        if entity_type == 'LOCATION' or entity_type == 'PERSON' or entity_type == 'ORGANIZATION':
                            if not text.isupper():
                                text = string.capwords(text)

                        if entity_type in entities:
                            entities[entity_type].add(text)
                        else:
                            entities[entity_type] = set([text])
        return entities
    else:
        return {}


def parse_speaker_segments(results):
    """
    From the Amazon Transcribe results JSON response, this function parses a list of all segments, their timeframe
    and associated speaker label. The individual 'items' field of each segment are not parsed

    :param results: Amazon Transcribe results JSON
    :return: List of segments with their time-frames and speaker labels
    """
    labelled_speaker_segments = results['speaker_labels']['segments']
    speaker_segments = []
    for label in labelled_speaker_segments:
        segment = dict()
        segment["start_time"] = float(label["start_time"])
        segment["end_time"] = float(label["end_time"])
        segment["speaker"] = label["speaker_label"]
        speaker_segments.append(segment)
    return speaker_segments


def get_speaker_label(speaker_segments, time_stamp):
    """
    Performs a linear search for the associated speaker for a given time_stamp
    TODO: Replace with more efficient search algorithm

    :param speaker_segments: List of speaker segments
    :param time_stamp: The time to search for in the list of speaker segments
    :return: Speaker label string if one exists, None otherwise
    """
    for segment in speaker_segments:
        if segment['start_time'] <= time_stamp < segment['end_time']:
            return segment['speaker']
    return None


def lambda_handler(event, context):
    """
        AWS Lambda handler
        Processes the result of the transcription using Amazon Comprehend, parses that result, and stores
        it in the S3 bucket
    """
    logger.info('Received event')
    logger.info(json.dumps(event))

    # Pull the signed URL for the payload of the transcription job
    transcription_url = event['transcribeStatus']['transcriptionUrl']

    vocab_info = None
    if 'vocabularyInfo' in event:
        vocab_info = event['vocabularyInfo']
    return process_transcript(transcription_url, vocab_info)
