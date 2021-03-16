import boto3
import time
import os
import string
import random

from elasticsearch import Elasticsearch, RequestsHttpConnection
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from requests_aws4auth import AWS4Auth

# Get AWS Clients
COMPREHEND = boto3.client(service_name='comprehend')
DYNAMODB = boto3.resource('dynamodb')
# dynamodb_client = boto3.client(service_name='dynamodb')
es_client = boto3.client('es')

TRANSCRIPT_INDEX = 'transcripts'

REGION = os.environ['AWS_REGION']
SERVICE = 'es'
CREDENTIALS = boto3.Session().get_credentials()

DOMAIN_NAME = os.environ['ES_DOMAIN']
CONTACT_DETAILS_TABLE = os.environ['CONTACT_TABLE_NAME']
CALL_TAKER_TABLE = os.environ['CALL_TAKER_TABLE_NAME']
JURISDICTIONS_TABLE = os.environ['JURISDICTION_TABLE_NAME']

JURISDICTIONS = [{'key': 'Vancouver', 'value': 'VPD'}, {'key': 'Abbotsford', 'value': 'APD'}]


def connectES():
    """
    Connects to the ElasticSearch domain with the specific credentials and returns a searchable domain
    """
    awsauth = AWS4Auth(CREDENTIALS.access_key,
                       CREDENTIALS.secret_key,
                       REGION, SERVICE,
                       session_token=CREDENTIALS.token)
    try:
        response = es_client.describe_elasticsearch_domain(DomainName=DOMAIN_NAME)
        es_host = response['DomainStatus']['Endpoint']
        es = Elasticsearch(hosts=[{'host': es_host, 'port': 443}], http_auth=awsauth,
                           use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
        return es
    except Exception as err:
        print("Unable to connect to ElasticSearch")
        print(err)
        exit(3)


def parse_jurisdiction(keyphrases):
    """
    Searches for pre-defined jurisdictions amongst the keyphrases (as substrings too), and returns
    the jurisdiction code if found
    :param keyphrases:
    :return:
    """
    jurisdiction_code = ''
    for jurisdiction_item in JURISDICTIONS:
        for keyphrase in keyphrases:
            if jurisdiction_item['key'] in keyphrase:
                jurisdiction_code = jurisdiction_item['value']

    if jurisdiction_code == '':
        jurisdiction_code = 'Undetermined'

    return jurisdiction_code


def handler(event, context):
    """
    Lambda entry point
    Retrieves the transcript text from dynamoDB, runs Comprehend to extract key_phrases and entities
    above 80% confidence, then performs a 'more like this' search of the transcript at the elasticsearch
    domain to get a list of recommended SOP's.
    Finally it inserts the contact ID of the call, the top 3 SOP's and the top jurisdiction into a
    DynamoDB table
    """
    for record in event.get('Records'):
        if record.get('eventName') in ('INSERT', 'MODIFY'):
            # Retrieve the item attributes from the stream record
            contact_id = record['dynamodb']['NewImage']['ContactId']['S']
            start_time = record['dynamodb']['NewImage']['StartTime']['N']
            end_time = record['dynamodb']['NewImage']['EndTime']['N']
            caller_transcript = record['dynamodb']['NewImage']['Transcript']['S']
            # is_partial = record['dynamodb']['NewImage']['IsPartial']['BOOL']

            # entities = []
            key_phrases = []
            SOPs = []
            keyphrase_list = []
            syntax_tokens = []

            # Designate a time period within the realtime call to call comprehend and query ES
            if 10 <= float(end_time) <= 120:

                call_taker_table = DYNAMODB.Table(CALL_TAKER_TABLE)
                query_result = call_taker_table.get_item(Key={"ContactId": contact_id}, ProjectionExpression="Transcript")

                try:
                    callee_transcript = query_result['Item']['Transcript']
                except KeyError as err:
                    callee_transcript = ''



                # compr_entities_result = compr.detect_entities(Text=transcript, LanguageCode='en')
                keyphrases_result = COMPREHEND \
                    .batch_detect_key_phrases(TextList=[caller_transcript, callee_transcript], LanguageCode='en')
                syntax_result = COMPREHEND \
                    .batch_detect_syntax(TextList=[caller_transcript, callee_transcript], LanguageCode='en')

                for result in keyphrases_result["ResultList"]:
                    keyphrase_list += result["KeyPhrases"]

                for result in syntax_result["ResultList"]:
                    syntax_tokens += result["SyntaxTokens"]

                # callee_keyphrases_result = COMPREHEND.detect_key_phrases(Text=callee_transcript, LanguageCode='en')
                # callee_syntax_result = COMPREHEND.detect_syntax(Text=callee_transcript, LanguageCode='en')

                # EntityList = compr_entities_result.get("Entities")
                # keyphrase_list = detect_keyphrases_result["KeyPhrases"]
                # syntax_tokens = detect_syntax_result["SyntaxTokens"]


                accuracy = 0.80

                # for s in EntityList:
                #     score = float(s.get("Score")) * 100
                #     if (score >= accuracy):
                #         entities.append(s.get("Text").strip('\t\n\r'))

                for keyphrase in keyphrase_list:
                    if float(keyphrase["Score"]) >= accuracy:
                        key_phrases.append(keyphrase["Text"].strip('\t\n\r'))

                for token in syntax_tokens:
                    if float(token["PartOfSpeech"]["Score"]) >= accuracy \
                            and token["PartOfSpeech"]["Tag"] == "VERB":
                        key_phrases.append(token["Text"].strip('\t\n\r'))

                key_phrases = list(dict.fromkeys(key_phrases))

                elastic_search_service = connectES()

                query_body = {
                    "query": {
                        "more_like_this": {
                            "fields": [
                                "key_phrases"
                            ],
                            "like": key_phrases,
                            "min_term_freq": 1,
                            "min_doc_freq": 2
                        }
                    }
                }

                es_result = elastic_search_service.search(index=TRANSCRIPT_INDEX, body=query_body, size=5)

                hits = es_result['hits']['hits']
                top_hits = hits[:3] if len(hits) > 3 else hits

                for hit in top_hits:
                    # print('%(procedure)s' % hit['_source'])
                    SOPs.append(hit['_source']['procedure'])

                SOP = ', '.join(SOPs) if len(SOPs) > 0 else 'Undetermined'

                jurisdiction = parse_jurisdiction(key_phrases)

                table = DYNAMODB.Table(CONTACT_DETAILS_TABLE)
                table.update_item(
                    Key={'ContactId': contact_id},
                    UpdateExpression='SET CallerTranscript = :var1,'
                                     'Keyphrases = :var2, RecommendedSOP = :var3, Jurisdiction = :var4',
                    ExpressionAttributeValues={':var1': caller_transcript, ':var2': key_phrases,
                                               ':var3': SOP, ':var4': jurisdiction}
                )
        else:
            print("Should only expect insert/modify DynamoDB operations")
