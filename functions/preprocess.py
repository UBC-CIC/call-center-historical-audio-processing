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
dynamodb = boto3.client('dynamodb')
es_client = boto3.client('es')

region = os.environ['AWS_REGION'] # 'us-west-2'
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
            print(contact_id)
            print(is_partial)
            print(transcript)
            print(start_time)
            print(end_time)

            textvalues=[]
            if (float(end_time) >= 60):
                compr_entities_result = compr.detect_entities(Text=transcript, LanguageCode='en')
                for resp in compr_entities_result['Entities']:
                    print(resp['Text'])
                    print(resp['Score'])
                compr_phrases_result = compr.detect_key_phrases(Text=transcript, LanguageCode='en')
                for resp in compr_phrases_result['KeyPhrases']:
                    print(resp['Text'])
                    print(resp['Score'])
                
                KeyPhraseList = compr_phrases_result.get("KeyPhrases")
                accuracy=85.0
                for s in KeyPhraseList:
                    score = float(s.get("Score"))*100
                    if (score >= accuracy):
                        textvalues.append(s.get("Text").strip('\t\n\r'))

                es = connectES()
                query_body = {
                    "query": {
                        "more_like_this": {
                            "fields": ['text'],
                            "like": textvalues,
                            "min_term_freq": 2,
                            "min_doc_freq": 2
                        }
                    }
                }
                result = es.search(index="ecomm-sop", body=query_body)
                for hit in result['hits']['hits']:
                    print('%(title)s' % hit["_source"])

                SOP_sample = result['hits']['hits'][0]['_source']['title']
                table = dynamodb.Table(contact_details_table)
                table.update_item(
                    Key={'ContactId': contact_id},
                    UpdateExpression='SET callerTranscript = :var1, recommendedSOP = :var2',
                    ExpressionAttributeValues={':var1': transcript, ':var2': SOP_sample}
                )
        else:
            print("Should only expect insert/modify DynamoDB operations")
