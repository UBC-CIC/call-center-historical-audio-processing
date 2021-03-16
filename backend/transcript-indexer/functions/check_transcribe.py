import boto3
import logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

transcribe_client = boto3.client('transcribe')


def lambda_handler(event, context):
    """
    Lambda function that checks if the transcribe job started by call_transcribe has finished
    Then it returns the transcription result obtained from Amazon Transcribe

    :param event All the event variables inside a dictionary
    :return: An transcription job results in event['transcribeStatus]
    """
    transcribe_job = event['callTranscribeResult']['transcribeJob']

    # Call the AWS SDK to get the status of the transcription job
    response = transcribe_client.get_transcription_job(TranscriptionJobName=transcribe_job)

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
