import boto3
import time
import os
import string
import random

dynamodb = boto3.resource('dynamodb')
contact_details_table = os.environ['CONTACT_TABLE_NAME']

def handler(event, context):
    try:
        table = dynamodb.Table(contact_details_table)
        scan_kwargs = {
            'ProjectionExpression': "ContactId, callTimestamp, customerPhoneNumber, callerTranscript, recommendedSOP, jurisdiction"
        }
        response = table.scan(**scan_kwargs)
        item_list = response.get('Items', [])
        response = {
              'isBase64Encoded': False,
              'statusCode': 200,
              'headers': {"Content-Type": "application/json"},
              'multiValueHeaders': {},
              'body': item_list
        }
        return response
    except:
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "body": "Error retrieving data",
            "headers": {"Content-Type": "application/json"}
        }

