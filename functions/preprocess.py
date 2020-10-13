import boto3
import time
import os
import string
import random

compr = boto3.client(service_name='comprehend')
s3 = boto3.client(service_name='s3')
lambda_client = boto3.client('lambda')

def check_time(stream_start_time):
    current_time_in_epoch_milliseconds = int(round(time.time() * 1000))
    return (current_time_in_epoch_milliseconds - stream_start_time) >= 3600

def handler(event, context):
    print("DynamoDB streams invoked, starting comprehend Lambda")
    print(os.environ)
    print(event)

    for record in event.get('Records'):
        if record.get('eventName') in ('INSERT', 'MODIFY'):
            
            # Retrieve the item attributes from the stream record
            start_time = event['dynamodb']['NewImage']['StartTime']['N']
            end_time = event['dynamodb']['NewImage']['EndTime']['N']
            transcript = event['dynamodb']['NewImage']['Transcript']['S']
            is_partial = event['dynamodb']['NewImage']['IsPartial']['BOOL']

            if not is_partial:
                print("The transcript not partial.")
                # pass the transcribed text through spellchecker and Comprehend
                # before passing through rules, invoke separate lambda function here
            print(is_partial)
            print(transcript)
            print(start_time)
            print(end_time)
        else:
            print("Not supported, should only expect insert/modify DynamoDB operations")
