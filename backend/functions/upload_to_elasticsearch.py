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
LOGGER = logging.getLogger()
if os.getenv('LOG_LEVEL') == 'DEBUG':
    LOGGER.setLevel(logging.DEBUG)
else:
    LOGGER.setLevel(logging.INFO)

# Parameters
REGION = os.getenv('AWS_REGION', default='us-east-1')

# Pull environment data for the ES domain
ES_ENDPOINT = os.environ['ES_DOMAIN']
# If debug mode is TRUE, then S3 files are not deleted
IS_DEBUG_MODE = os.environ['DEBUG_MODE']

# get the Elasticsearch index name from the environment variables
ES_INDEX = os.getenv('ES_INDEX', default='transcripts')

S3_CLIENT = boto3.client('s3')
# Create the auth token for the sigv4 signature
SESSION = boto3.session.Session()
CREDENTIALS = SESSION.get_credentials().get_frozen_credentials()
AWS_AUTH = AWSRequestsAuth(
    aws_access_key=CREDENTIALS.access_key,
    aws_secret_access_key=CREDENTIALS.secret_key,
    aws_token=CREDENTIALS.token,
    aws_host=ES_ENDPOINT,
    aws_region=REGION,
    aws_service='es'
)

# Connect to the elasticsearch cluster using aws authentication. The lambda function
# must have access in an IAM policy to the ES cluster.
ES_CLIENT = Elasticsearch(
    hosts=[{'host': ES_ENDPOINT, 'port': 443}],
    http_auth=AWS_AUTH,
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
    The transcript is deleted afterwards in non-debug mode (stored as a environment variable)
    """
    call_transcript_s3_location = event["processTranscriptionResult"]
    index_transcript(event, call_transcript_s3_location)

    if IS_DEBUG_MODE != 'TRUE':
        # Deletes the audio files in the amplify frontend storage bucket
        response = S3_CLIENT.delete_object(Bucket=event['bucketName'], Key=event['bucketKey'])

    return


def index_transcript(event, call_transcript_s3_location):
    # Retrieves the transcribed text file stored in S3
    response = S3_CLIENT.get_object(Bucket=call_transcript_s3_location['bucket'],
                                    Key=call_transcript_s3_location['key'])
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
        'key_phrases': full_call_transcript['key_phrases']
    }

    LOGGER.info("request")
    LOGGER.debug(json.dumps(doc))

    # add the document to the index
    start = time.time()
    res = ES_CLIENT.index(index=ES_INDEX, body=doc, id=event['dynamoId'])
    LOGGER.info("response")
    LOGGER.info(json.dumps(res, indent=4))
    LOGGER.info('REQUEST_TIME es_client.index {:10.4f}'.format(time.time() - start))
