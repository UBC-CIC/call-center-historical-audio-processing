import boto3
import time
import os
import string
import random

from elasticsearch import Elasticsearch, RequestsHttpConnection
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from requests_aws4auth import AWS4Auth

compr = boto3.client(service_name='comprehend')
dynamodb = boto3.resource('dynamodb')
es_client = boto3.client('es')

TRANSCRIPT_INDEX = 'transcripts'

region = os.environ['AWS_REGION']
service = 'es'
credentials = boto3.Session().get_credentials()

domain_name = os.environ['ES_DOMAIN']
contact_details_table = os.environ['CONTACT_TABLE_NAME']

def connectES():
    awsauth = AWS4Auth(credentials.access_key, 
    credentials.secret_key, 
    region, service,
    session_token=credentials.token)
    try:
        response = es_client.describe_elasticsearch_domain(DomainName=domain_name)
        es_host = response['DomainStatus']['Endpoint']

        es = Elasticsearch(hosts=[{'host': es_host, 'port': 443}], http_auth = awsauth,
        use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
        return es
    except Exception as err:
        print("Unable to connect to {0}")
        print(err)
        exit(3)

def handler(event, context):
    print("DynamoDB streams invoked, starting comprehend Lambda")

    for record in event.get('Records'):
        if record.get('eventName') in ('INSERT', 'MODIFY'):
            # Retrieve the item attributes from the stream record
            contact_id = record['dynamodb']['NewImage']['ContactId']['S']
            start_time = record['dynamodb']['NewImage']['StartTime']['N']
            end_time = record['dynamodb']['NewImage']['EndTime']['N']
            transcript = record['dynamodb']['NewImage']['Transcript']['S']
            is_partial = record['dynamodb']['NewImage']['IsPartial']['BOOL']

            locations = []
            key_phrases = []
            SOPs = []

            # designate a time period within the realtime call to call comprehend and query ElasticSearch
            if (float(end_time) >= 60 and float(end_time) <= 120):
                compr_entities_result = compr.detect_entities(Text=transcript, LanguageCode='en')
                compr_phrases_result = compr.detect_key_phrases(Text=transcript, LanguageCode='en')
                
                EntityList = compr_entities_result.get("Entities")
                KeyPhraseList = compr_phrases_result.get("KeyPhrases")
                accuracy=80.0

                for s in EntityList:
                    score = float(s.get("Score"))*100
                    if (score >= accuracy and s.get("Type") == "LOCATION"):
                        locations.append(s.get("Text").strip('\t\n\r'))

                for s in KeyPhraseList:
                    score = float(s.get("Score"))*100
                    if (score >= accuracy):
                        key_phrases.append(s.get("Text").strip('\t\n\r'))

                print(locations)

                es = connectES()

                query_body = {
                    "query": {
                        "more_like_this": {
                            "fields": [
                                'transcript'
                            ],
                            "like": transcript,
                            "min_term_freq": 1,
                            "min_doc_freq": 2
                        }
                    }
                }
                
                result = es.search(index=TRANSCRIPT_INDEX, body=query_body)

                hits = result['hits']['hits']
                top_hits = hits[:3] if len(hits) > 3 else hits
                
                for hit in top_hits:
                    print('%(procedure)s' % hit['_source'])
                    SOPs.append(hit['_source']['procedure'])

                SOP = ', '.join(SOPs) if len(SOPs) > 0 else 'Undetermined'
                jurisdiction = 'Undetermined' if len(locations) == 0 else locations[0]

                table = dynamodb.Table(contact_details_table)
                table.update_item(
                    Key={'ContactId': contact_id},
                    UpdateExpression='SET callerTranscript = :var1, recommendedSOP = :var2, jurisdiction = :var3',
                    ExpressionAttributeValues={':var1': transcript, ':var2': SOP, ':var3': jurisdiction}
                )
        else:
            print("Should only expect insert/modify DynamoDB operations")
