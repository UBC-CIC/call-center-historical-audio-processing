from __future__ import print_function

import boto3
import certifi
import json
import os
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import logging
import time

# Log level
logging.basicConfig()
logger = logging.getLogger()
if os.getenv('LOG_LEVEL') == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Parameters
REGION = os.getenv('AWS_REGION', default='us-east-1')

# Pull environment data for the ES domain
esendpoint = os.environ['ES_DOMAIN']
# If debug mode is TRUE, then S3 files are not deleted
isDebugMode = os.environ['DEBUG_MODE']

# get the Elasticsearch index name from the environment variables
ES_INDEX = os.getenv('ES_INDEX', default='transcripts')
# get the Elasticsearch index name from the environment variables

s3_client = boto3.client('s3')
# Create the auth token for the sigv4 signature
session = boto3.session.Session()
credentials = session.get_credentials().get_frozen_credentials()
awsauth = AWSRequestsAuth(
    aws_access_key=credentials.access_key,
    aws_secret_access_key=credentials.secret_key,
    aws_token=credentials.token,
    aws_host=esendpoint,
    aws_region=REGION,
    aws_service='es'
)

# Connect to the elasticsearch cluster using aws authentication. The lambda function
# must have access in an IAM policy to the ES cluster.
es = Elasticsearch(
    hosts=[{'host': esendpoint, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    ca_certs=certifi.where(),
    timeout=120,
    connection_class=RequestsHttpConnection
)


# Entry point into the lambda function
def lambda_handler(event, context):
    """
    Lambda handler executed after transcription is processed. This function takes the the processed transcription
    and indexes it into the ElasticSearch.
    The transcript is deleted afterwards
    """
    full_call_transcript_s3_location = event["processTranscriptionResult"]
    index_transcript(es, event, full_call_transcript_s3_location)

    if isDebugMode != 'TRUE':
        # Deletes the audio files in the amplify frontend storage bucket
        response = s3_client.delete_object(Bucket=event['bucketName'], Key=event['bucketKey'])

    return


def index_transcript(elasticsearch, event, full_call_transcript_s3_location):
    # Retrieves the transcribed text file stored in S3
    response = s3_client.get_object(Bucket=full_call_transcript_s3_location['bucket'],
                                    Key=full_call_transcript_s3_location['key'])
    file_content = response['Body'].read().decode('utf-8')
    full_call_transcript = json.loads(file_content)

    s3_location = "s3://" + event['bucketName'] + "/" + event['bucketKey']

    # Metadata of the processed transcript that is indexed in elasticsearch
    doc = {
        'audio_type': event['fileType'],
        'name': event['fileName'],
        'jurisdiction': event['jurisdiction'],
        'description': event['description'],
        'procedure': event['procedure'],
        'audio_s3_location': s3_location,
        'transcript':  full_call_transcript['transcript'],
        # 'transcript_entities':  full_call_transcript['transcript_entities'],
        'key_phrases': full_call_transcript['key_phrases']
    }

    logger.info("request")
    logger.debug(json.dumps(doc))

    # add the document to the index
    start = time.time()
    res = elasticsearch.index(index=ES_INDEX,
                              body=doc, id=event['dynamoId'])
    logger.info("response")
    logger.info(json.dumps(res, indent=4))
    logger.info('REQUEST_TIME es_client.index {:10.4f}'.format(time.time() - start))
