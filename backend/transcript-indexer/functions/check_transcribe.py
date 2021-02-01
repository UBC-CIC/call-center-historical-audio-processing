from __future__ import print_function
import boto3
from botocore.client import Config
import datetime


# The entry point for the lambda function
def lambda_handler(event, context):
    """
    Lambda function that takes the transcribe job event and checks it if has completed the transcription task
    """
    transcribeJob = event['transcribeJob']
    transcribe_client = boto3.client('transcribe')

    # Call the AWS SDK to get the status of the transcription job
    response = transcribe_client.get_transcription_job(TranscriptionJobName=transcribeJob)

    # Pull the status
    status = response['TranscriptionJob']['TranscriptionJobStatus']

    retval = {
        "status": status
    }

    # If the status is completed, return the transcription file url. This will be a signed url
    # that will provide the full details on the transcription
    # Otherwise it returns the non-completed status of the transcribe request
    if status == 'COMPLETED':
        retval["transcriptionUrl"] = response['TranscriptionJob']['Transcript']['RedactedTranscriptFileUri']

    return retval