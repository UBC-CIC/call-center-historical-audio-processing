import boto3
import os
from common_lib import id_generator
import logging
from botocore.config import Config

# Log level
logging.basicConfig()
logger = logging.getLogger()
if os.getenv('LOG_LEVEL') == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Get AWS region and necessary clients
REGION = boto3.session.Session().region_name

# Limit the number of retries submitted by boto3 because Step Functions will
# handle the exponential retries more efficiently
CONFIG = Config(
    retries=dict(
        max_attempts=2
    )
)
transcribe_client = boto3.client('transcribe', config=CONFIG)


CONTENT_TYPE_TO_MEDIA_FORMAT = {
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/flac": "flac",
    "audio/mp4a-latm": "mp4"}


class InvalidInputError(ValueError):
    pass


class TranscribeException(Exception):
    # Does nothing for this file but stops the lambda from returning any values
    pass


def lambda_handler(event, context):
    """
    Upon successful upload of an audio file, this lambda handler takes the audio and
    starts an audio transcription request via Amazon Transcribe

    :param event: All event variables including request params in `start_trigger.py` lambda
    :return: A dict for the `check_transcribe.py` lambda handler
    """

    # Default to unsuccessful
    is_successful = "FALSE"

    # Create a random name for the transcription job
    jobname = id_generator()

    # Extract the bucket and key
    bucket = event['bucketName']
    key = event['bucketKey']

    # Get the appropriate media file format
    content_type = event['fileType']
    if content_type not in CONTENT_TYPE_TO_MEDIA_FORMAT:
        raise InvalidInputError(f"{content_type} is not supported audio type.")
    media_format = CONTENT_TYPE_TO_MEDIA_FORMAT[content_type]
    logger.info(f"media type: {content_type}")

    # Assemble the url for the object for transcribe. It must be an s3 url in the region
    url = f"https://s3-{REGION}.amazonaws.com/{bucket}/{key}"

    try:
        settings = {
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': 2
        }

        # Call the AWS SDK to initiate the transcription job.
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=jobname,
            LanguageCode='en-US',
            Settings=settings,
            MediaFormat=media_format,
            Media={
                'MediaFileUri': url
            },
            ContentRedaction={
                'RedactionType': 'PII',
                'RedactionOutput': 'redacted'
            }
        )
        is_successful = "TRUE"

    except transcribe_client.exceptions.BadRequestException as e:
        # Issues in the configuration of the transcribe request
        logger.error(str(e))
        raise TranscribeException(e)
    except transcribe_client.exceptions.LimitExceededException as e:
        # There is a limit to how many transcribe jobs can run concurrently. If you hit this limit,
        # return unsuccessful and the step function will retry.
        logger.error(str(e))
        raise TranscribeException(e)
    except transcribe_client.exceptions.ClientError as e:
        logger.error(str(e))
        raise TranscribeException(e)

    # Return the transcription job and the success code only if there are no errors in the transcription request
    return {
        "success": is_successful,
        "transcribeJob": jobname
    }
