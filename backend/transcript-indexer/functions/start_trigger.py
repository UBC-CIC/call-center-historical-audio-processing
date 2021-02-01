import boto3
import time
import os
import string
import random
import json

from common_lib import id_generator

def lambda_handler(event, context):
    """
    Start the state machine that triggers audio transcription and processing
    This is the first lambda function that runs
    """
    stepfunctions_client = boto3.client('stepfunctions')
    stepFunctionArn = os.environ['STEP_FUNCTION_ARN']

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

            requestParams = {
                "dynamoId": Id,
                "bucketName": BucketName,
                "bucketKey": BucketKey,
                "jurisdiction": Jurisdiction,
                "description": Description,
                "procedure": Procedure,
                "fileType": FileType,
                "fileName": FileName
            }

            response = stepfunctions_client.start_execution(
                stateMachineArn=stepFunctionArn,
                name=id_generator(),
                input=json.dumps(requestParams, indent=4, sort_keys=True, default=str)
            )
        else:
            print("Should only expect insert/modify DynamoDB operations")
