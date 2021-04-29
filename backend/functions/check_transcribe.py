import boto3
import logging

logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

TRANSCRIBE_CLIENT = boto3.client('transcribe')


def lambda_handler(event, context):
    """
    Second Lambda function in the step functions workflow. It checks if the Transcribe job has finished,
    if not, it runs again to check after 60 seconds.
    If the Transcribe Job has finished, it returns the Transcribe url whose payload can be read to retrieve
    the audio transcript with personal information redacted


    :param event: All the event variables inside a dictionary
    :return: An transcription job results in event['transcribeUrl']
    """
    transcribe_job = event['callTranscribeResult']['transcribeJob']

    # Call the AWS SDK to get the status of the transcription job
    response = TRANSCRIBE_CLIENT.get_transcription_job(TranscriptionJobName=transcribe_job)

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
