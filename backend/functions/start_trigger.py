import boto3
import os
import json
from common_lib import id_generator

STEPFUNCTIONS_CLIENT = boto3.client('stepfunctions')
STEPFUNCTIONS_ARN = os.environ['STEP_FUNCTION_ARN']


def lambda_handler(event, context):
    """
    The first lambda function that runs, triggered by a DynamoDB Transcripts table event
    Starts the state machine and gives it the key for audio file stored in S3 for audio transcription
    Does not return any value for another lambda function
    """

    for record in event.get('Records'):
        if record.get('eventName') in ('INSERT', 'MODIFY'):

            # Retrieve the item attributes from the stream record
            Id = record['dynamodb']['NewImage']['id']['S']
            Procedure = record['dynamodb']['NewImage']['procedure']['S']
            BucketName = record['dynamodb']['NewImage']['fileData']['M']['bucketName']['S']
            BucketKey = record['dynamodb']['NewImage']['fileData']['M']['bucketKey']['S']
            Jurisdiction = record['dynamodb']['NewImage']['jurisdiction']['S']
            Description = record['dynamodb']['NewImage']['description']['S']
            FileType = record['dynamodb']['NewImage']['fileType']['S']
            FileName = record['dynamodb']['NewImage']['fileName']['S']

            request_params = {
                "dynamoId": Id,
                "bucketName": BucketName,
                "bucketKey": BucketKey,
                "jurisdiction": Jurisdiction,
                "description": Description,
                "procedure": Procedure,
                "fileType": FileType,
                "fileName": FileName
            }

            response = STEPFUNCTIONS_CLIENT.start_execution(
                stateMachineArn=STEPFUNCTIONS_ARN,
                name=id_generator(),
                input=json.dumps(request_params, indent=4, sort_keys=True, default=str)
            )
        else:
            print("Should only expect insert/modify DynamoDB operations")
