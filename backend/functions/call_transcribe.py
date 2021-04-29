import boto3
import os
from common_lib import id_generator
import logging
from botocore.config import Config

# Log level
logging.basicConfig()
LOGGER = logging.getLogger()
if os.getenv('LOG_LEVEL') == 'DEBUG':
    LOGGER.setLevel(logging.DEBUG)
else:
    LOGGER.setLevel(logging.INFO)

# Get AWS region and necessary clients
REGION = boto3.session.Session().region_name

# Limit the number of retries submitted by boto3 because Step Functions will
# handle the exponential retries more efficiently
CONFIG = Config(
    retries=dict(
        max_attempts=2
    )
)
TRANSCRIBE_CLIENT = boto3.client('transcribe', config=CONFIG)


CONTENT_TYPE_TO_MEDIA_FORMAT = {
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/flac": "flac",
    "audio/mp4a-latm": "mp4"}


class InvalidInputError(ValueError):
    """
    Error raised on invalid input file type to Transcribe
    """
    pass


class TranscribeException(Exception):
    """
    Error raised on Transcribe request formatting
    """
    pass


def lambda_handler(event, context):
    """
    The first function in the step functions workflow. It starts a Transcribe request for the audio file
    uploaded to S3

    :param event: Input that is passed in when `start_trigger.py` starts the step functions workflow
    :return: A dict for the `check_transcribe.py` lambda
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
    LOGGER.info(f"media type: {content_type}")

    # Assemble the url for the object for transcribe. It must be an s3 url in the region
    url = f"https://s3-{REGION}.amazonaws.com/{bucket}/{key}"

    try:
        settings = {
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': 2
        }

        # Call the AWS SDK to initiate the transcription job.
        response = TRANSCRIBE_CLIENT.start_transcription_job(
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

    except TRANSCRIBE_CLIENT.exceptions.BadRequestException as e:
        # Issues in the configuration of the transcribe request
        LOGGER.error(str(e))
        raise TranscribeException(e)
    except TRANSCRIBE_CLIENT.exceptions.LimitExceededException as e:
        # There is a limit to how many transcribe jobs can run concurrently. If you hit this limit,
        # return unsuccessful and the step function will retry.
        LOGGER.error(str(e))
        raise TranscribeException(e)
    except TRANSCRIBE_CLIENT.exceptions.ClientError as e:
        LOGGER.error(str(e))
        raise TranscribeException(e)

    # Return the transcription job and the success code only if there are no errors in the transcription request
    return {
        "success": is_successful,
        "transcribeJob": jobname
    }
