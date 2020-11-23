""" Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. 
A copy of the License is located at: http://aws.amazon.com/apache2.0/
This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
See the License for the specific language governing permissions and limitations under the License. """

from __future__ import print_function
from elasticsearch import Elasticsearch, RequestsHttpConnection
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from requests_aws4auth import AWS4Auth
import os
import os.path
import sys
import tempfile
import boto3
import json
import PyPDF2 
try:
    from urllib.parse import unquote_plus
except ImportError:
     from urllib import unquote_plus

root = os.environ["LAMBDA_TASK_ROOT"]
sys.path.insert(0, root)
print('core path setup')
s3 = boto3.resource('s3')
s3client = boto3.client('s3')
comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
host= os.environ['esDomain']

#host = 'search-resumetestdomain-5mtjmaplk3hvdyxigqx7lazdbq.us-east-1.es.amazonaws.com' 
# For example, my-test-domain.us-east-1.es.amazonaws.com

region = 'us-west-2'
service = 'es'
credentials = boto3.Session().get_credentials()

def connectES():
 print ('Connecting to the ES Endpoint {0}')
 awsauth = AWS4Auth(credentials.access_key, 
 credentials.secret_key, 
 region, service,
 session_token=credentials.token)
 try:
  es = Elasticsearch(
   hosts=[{'host': host, 'port': 443}],
   http_auth = awsauth,
   use_ssl=True,
   verify_certs=True,
   connection_class=RequestsHttpConnection)
  return es
 except Exception as E:
  print("Unable to connect to {0}")
  print(E)
  exit(3)

# --------------- Main Lambda Handler ------------------


def handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'])
    print("key is"+key)
    print("bucket is"+bucket)
    textvalues=[]
    textvalues_entity={}
    text=""
    try:
        s3.Bucket(bucket).download_file(Key=key,Filename='/tmp/{}')
        print("Object downloaded")
        pdfFileObj = open('/tmp/{}', 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj) 
        num_pages = pdfReader.numPages
        title = pdfReader.getDocumentInfo().title

        print("number of pages")
        print(num_pages)

        print("number of pages")
        print(title)

        count = 0
        extracted_pdftext = ""
        searchable_text=[]

        while count < num_pages:
            pageObj = pdfReader.getPage(count)
            count +=1
            print(count)
            print("-------------iteration starts---------")
            extracted_pdftext = pageObj.extractText()
            if(sys.getsizeof(extracted_pdftext)> 5000):
                text = extracted_pdftext[:5000]
                text.strip('\t\n\r')
            else:
                text=extracted_pdftext.strip('\t\n\r')
            searchable_text.append(text)
            # Extracting Key Phrases
            print(text)
            sentiment_response = comprehend.detect_key_phrases(Text=text, LanguageCode='en')
            KeyPhraseList=sentiment_response.get("KeyPhrases")
            accuracy=90.0
            for s in KeyPhraseList:
                score=float(s.get("Score"))*100
                if(score >= accuracy):
                    textvalues.append(s.get("Text").strip('\t\n\r'))
                    
            detect_entity= comprehend.detect_entities(Text=text, LanguageCode='en')
             #print(detect_entity)
            EntityList=detect_entity.get("Entities")
            #print(EntityList)
            for s in EntityList:
                score=float(s.get("Score"))*100
                if(score >= accuracy):
                    textvalues_entity.update([(s.get("Type").strip('\t\n\r'),s.get("Text").strip('\t\n\r'))])
            
        pdfFileObj.close() 
        #https://s3.console.aws.amazon.com/s3/object/%3Cbucket%3E/%3Ckey%3E?region=us-east-1
        s3url= 'https://s3.console.aws.amazon.com/s3/object/'+bucket+'/'+key+'?region=us-east-1'
        search_data={'s3link':s3url,'KeyPhrases':textvalues,'Entity':textvalues_entity,'text':searchable_text, 'title':title}
        print(search_data)

        es=connectES()
        es.index(index="ecomm-sop", doc_type="_doc", body=search_data)
        return 'keyphrases Successfully Uploaded'

    except Exception as e:
        print(e)
        print('Error: ')
        raise e
