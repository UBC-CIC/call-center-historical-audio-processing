import boto3
import os
import logging
import time
import json
from urllib.request import urlopen
from common_lib import id_generator

# Logging configurations
logging.basicConfig()
LOGGER = logging.getLogger()
if os.getenv('LOG_LEVEL') == 'DEBUG':
    LOGGER.setLevel(logging.DEBUG)
else:
    LOGGER.setLevel(logging.INFO)

# Environment Parameters
REGION = os.getenv('AWS_REGION', default='us-east-1')
# Pull the bucket name from the environment variable set in the cloudformation stack
# This bucket is used for storing text transcripts
BUCKET = os.environ['BUCKET_NAME']
LOGGER.info(f"bucket: {BUCKET}")

# Global Parameters
COMMON_DICT = {'i': 'I'}
KEY_PHRASES_CONFIDENCE_THRESHOLD = 0.5

# Get the necessary AWS tools
S3_CLIENT = boto3.client("s3")
COMPREHEND_CLIENT = boto3.client(service_name='comprehend', region_name=REGION)


class InvalidInputError(ValueError):
    pass


def process_transcript(transcription_url, vocabulary_info):
    """
    Processes the transcript and returns the S3 bucket URI of processed transcript

    :param transcription_url: A signed url that contains the audio transcription result from Transcribe
    :param vocabulary_info: Custom vocabulary for transcription if implemented
    :return: A dict containing the bucket location for the transcribed text
    """
    custom_vocabs = None

    # Read Transcribe result url
    response = urlopen(transcription_url)
    output = response.read()
    json_data = json.loads(output)

    LOGGER.debug(json.dumps(json_data, indent=4))
    results = json_data['results']
    # free up memory
    del json_data

    comprehend_text, speaker_labelled_paragraphs = chunk_up_transcript(custom_vocabs, results)

    start = time.time()
    detected_phrase_response = COMPREHEND_CLIENT.batch_detect_key_phrases(TextList=comprehend_text, LanguageCode='en')
    round_trip = time.time() - start
    LOGGER.info('End of batch_detect_key_phrases. Took time {:10.4f}\n'.format(round_trip))

    key_phrases = parse_detected_key_phrases_response(detected_phrase_response)
    LOGGER.debug(json.dumps(key_phrases, indent=4))

    start = time.time()
    syntax_results = COMPREHEND_CLIENT.batch_detect_syntax(TextList=comprehend_text, LanguageCode='en')
    round_trip = time.time() - start
    LOGGER.info('End of batch_detect_syntax. Took time {:10.4f}\n'.format(round_trip))

    extra_keywords = parse_verbs_from_syntaxes(syntax_results)

    key_phrases.extend(extra_keywords)
    LOGGER.info(f"Final keyphrases:{key_phrases}")

    doc_to_update = {'transcript': speaker_labelled_paragraphs,
                     # 'transcript_entities': entities,
                     'key_phrases': key_phrases}
    LOGGER.debug(json.dumps(doc_to_update, indent=4))

    key = f'calls/transcript/{id_generator()}.json'

    response = S3_CLIENT.put_object(Body=json.dumps(doc_to_update, indent=2), Bucket=BUCKET, Key=key)
    LOGGER.debug(json.dumps(response, indent=2))

    LOGGER.info(f"successfully written transcript to s3://{BUCKET}/{key}")
    # Return the bucket and key of the transcription / comprehend result.
    transcript_location = {"bucket": BUCKET, "key": key}
    return transcript_location


def chunk_up_transcript(custom_vocabs, results):
    """
    Takes the result from Amazon Transcribe, breaks it down into two lists with
    chunks of text, paragraphs with speaker labels and raw spoken text for AWS Comprehend processing. The
    resulting text is updated with both a custom vocabulary that is passed in and a global
    vocabulary that exists as a global parameter

    :param custom_vocabs: Custom vocabulary mapping Transcribe response to an arbitrary string depending on use case
    :param results: the JSON response from Amazon Transcribe
    :return: comprehend_text: A list of 4500+ word chunks to be sent to Amazon Comprehend for interpretation
             speaker_labelled_paragraphs: A list of Transcribe text broken down into small chunks and
             separated by speaker labels
    """
    # Here is the JSON format returned by the Amazon Transcription SDK
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.get_transcription_job
    # Entire output examples can be found here
    # https://github.com/kibaffo33/aws_transcribe_to_docx/tree/master/sample_material

    speaker_label_exist = False
    speaker_segments = None
    # If the transcription has speaker labels, parse the individual segments of speech into a list
    if 'speaker_labels' in results:
        speaker_label_exist = True
        speaker_segments = parse_speaker_segments(results)

    transcribed_units = results['items']
    last_speaker = None
    speaker_labelled_paragraphs = []
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
                        speaker_labelled_paragraphs.append(current_paragraph)
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
                    speaker_labelled_paragraphs.append(current_paragraph)
                current_paragraph = ""

            # Get the transcribed item, replace content with custom and global vocabulary,
            # then add it to the current_paragraph
            phrase = item['alternatives'][0]['content']
            if custom_vocabs is not None:
                if phrase in custom_vocabs:
                    phrase = custom_vocabs[phrase]
                    LOGGER.info("replaced custom vocab: " + phrase)
            if phrase in COMMON_DICT:
                phrase = COMMON_DICT[phrase]
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
        speaker_labelled_paragraphs.append(current_paragraph)

    LOGGER.debug(json.dumps(speaker_labelled_paragraphs, indent=4))
    LOGGER.debug(json.dumps(comprehend_chunks, indent=4))

    return comprehend_chunks, "\n\n".join(speaker_labelled_paragraphs)


# def parse_detected_entities_response(detected_entities_response, entities):
#     """
#     Takes the output of Amazon Comprehend batch_detect_entities and parses it by doing the following
#
#     * It logs the ErrorList, i.e text that failed entity detection
#     * Filters the ResultList by only keeping entities above the ENTITY_CONFIDENCE_THRESHOLD and entities that are not of type QUANTITY
#     * Keeps non-duplicate entities only
#
#     :param detected_entities_response: Response JSON from Amazon Comprehend batch_detect_entities()
#     :param entities: a dict containing sets of entities for each type of entity (initially empty)
#     :return: a dict containing list of entities for each type of entity kept (e.g LOCATION, PERSON etc)
#     """
#     if 'ErrorList' in detected_entities_response and len(detected_entities_response['ErrorList']) > 0:
#         LOGGER.error("encountered error during batch_detect_entities")
#         LOGGER.error("error:" + json.dumps(detected_entities_response['ErrorList'], indent=4))
#
#     if 'ResultList' in detected_entities_response:
#         result_list = detected_entities_response["ResultList"]
#         for result in result_list:
#             detected_entities = result["Entities"]
#             for detected_entity in detected_entities:
#                 if float(detected_entity["Score"]) >= ENTITY_CONFIDENCE_THRESHOLD:
#                     entity_type = detected_entity["Type"]
#
#                     if entity_type != 'QUANTITY':
#                         entity_label = detected_entity["Text"]
#
#                         if entity_type in entities:
#                             entities[entity_type].add(entity_label)
#                         else:
#                             entities[entity_type] = {entity_label}
#
#         entity_dict = {}
#         for entity_type in entities:
#             entity_dict[entity_type] = list(entities[entity_type])
#         return entity_dict
#     else:
#         return {}


def parse_detected_key_phrases_response(detected_phrase_response):
    """
    Given the result of batch_detect_key_phrases from Amazon Comprehend
    It logs the ErrorList,
    returns a list of key_phrases that are above KEY_PHRASES_CONFIDENCE_THRESHOLD with no duplicate entries

    :param detected_phrase_response: Response from Amazon Comprehend for batch_detect_key_phrases
    :return: a list of noun key_phrases with no duplicates
    """
    if 'ErrorList' in detected_phrase_response and len(detected_phrase_response['ErrorList']) > 0:
        LOGGER.error("encountered error during batch_detect_key_phrases")
        LOGGER.error(json.dumps(detected_phrase_response['ErrorList'], indent=4))

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


def parse_verbs_from_syntaxes(syntax_results):
    """
    Given the result of batch_detect_key_phrases from Amazon Comprehend
    It logs the ErrorList,
    returns a list of key_phrases that are above KEY_PHRASES_CONFIDENCE_THRESHOLD with no duplicate entries

    :param syntax_results: Response from Amazon Comprehend for batch_detect_key_phrases
    :return: a list of noun key_phrases with no duplicates
    """
    if 'ErrorList' in syntax_results and len(syntax_results['ErrorList']) > 0:
        LOGGER.error("encountered error during batch_detect_syntax")
        LOGGER.error(json.dumps(syntax_results['ErrorList'], indent=4))
    keywords = set()
    if 'ResultList' in syntax_results:
        result_list = syntax_results["ResultList"]
        for result in result_list:
            tokens = result['SyntaxTokens']
            for token in tokens:
                if float(token['PartOfSpeech']['Score']) > KEY_PHRASES_CONFIDENCE_THRESHOLD\
                        and token_is_adjective_or_adverb(token['PartOfSpeech']['Tag']):
                    keywords.add(token['Text'])

    return list(keywords)


def token_is_adjective_or_adverb(tag):
    return tag == 'ADJ' or tag == 'VERB'


def parse_speaker_segments(results):
    """
    From the Amazon Transcribe results JSON response, this function parses a list of all segments, their timeframe
    and associated speaker label. The individual 'items' key of each segment are not parsed

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

        :return A dict containing the transcription bucket and key, returned in event['processedTranscription']
                for `upload_to_elasticsearch.py` lambda handler
    """
    LOGGER.info('Received transcription url')
    LOGGER.info(json.dumps(event))

    # Pull the signed URL for the payload of the transcription job
    transcription_url = event['checkTranscribeResult']['transcriptionUrl']

    vocab_info = None
    # NOTE: Custom vocabulary may be inserted here
    if 'vocabularyInfo' in event:
        vocab_info = event['vocabularyInfo']
    return process_transcript(transcription_url, vocab_info)
