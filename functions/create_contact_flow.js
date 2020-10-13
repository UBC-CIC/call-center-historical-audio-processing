/**********************************************************************************************************************
 *  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved                                            *
 *                                                                                                                    *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated      *
 *  documentation files (the "Software"), to deal in the Software without restriction, including without limitation   *
 *  the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and  *
 *  to permit persons to whom the Software is furnished to do so.                                                     *
 *                                                                                                                    *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO  *
 *  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    *
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF         *
 *  CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS *
 *  IN THE SOFTWARE.                                                                                                  *
 **********************************************************************************************************************/
'use strict';

function createContactFlow(properties, callback) {
    if (!properties.bucketName)
        callback("Bucket name not specified");

    var aws = require("aws-sdk");
    var S3 = new aws.S3();

    console.log('Event Details', properties);
    var lambdaInitArn = properties.contactInitFunction;
    var lambdaTriggerArn = properties.kvsTriggerFunction;
    var bucketName = properties.bucketName;

    var mainFlow = `{"modules":[{"id":"856dd865-e5a0-49c6-aacc-55fe53c38a22","type":"SetLoggingBehavior","branches":[{"condition":"Success","transition":"53e6aa2b-e374-4ae6-bfc9-1285d2ac202f"}],"parameters":[{"name":"LoggingBehavior","value":"Enable"}],"metadata":{"position":{"x":181,"y":16}}},{"id":"53e6aa2b-e374-4ae6-bfc9-1285d2ac202f","type":"SetRecordingBehavior","branches":[{"condition":"Success","transition":"6728609a-9707-41f7-a87c-30ac1fde4f4c"}],"parameters":[{"name":"RecordingBehaviorOption","value":"Enable"},{"name":"RecordingParticipantOption","value":"Both"}],"metadata":{"position":{"x":393,"y":13}}},{"id":"6728609a-9707-41f7-a87c-30ac1fde4f4c","type":"StartMediaStreaming","branches":[{"condition":"Success","transition":"abe8c2b7-f002-41b1-8e9e-374ff32c2351"},{"condition":"Error","transition":"410057d0-9390-486b-bbb4-c4def2a7367c"}],"parameters":[{"name":"Track","value":"FromCustomer"},{"name":"Track","value":"ToCustomer"},{"name":"MediaStreamTypes","value":"Audio"}],"metadata":{"position":{"x":162,"y":222},"fromCustomer":true,"toCustomer":true}},{"id":"410057d0-9390-486b-bbb4-c4def2a7367c","type":"PlayPrompt","branches":[{"condition":"Success","transition":"99458f47-6941-48ce-9b90-fdf184759b22"}],"parameters":[{"name":"Text","value":"An error occurred when we tried to start streaming.","namespace":null},{"name":"TextToSpeechType","value":"text"}],"metadata":{"position":{"x":144,"y":702},"useDynamic":false}},{"id":"919982d6-3066-49e5-afe5-619896781245","type":"Transfer","branches":[{"condition":"AtCapacity","transition":"04aacf02-1a6a-4df8-9a3b-5cce1d6e25a4"},{"condition":"Error","transition":"04aacf02-1a6a-4df8-9a3b-5cce1d6e25a4"}],"parameters":[],"metadata":{"position":{"x":952,"y":318},"useDynamic":false,"queue":null},"target":"Queue"},{"id":"04aacf02-1a6a-4df8-9a3b-5cce1d6e25a4","type":"Disconnect","branches":[],"parameters":[],"metadata":{"position":{"x":1212,"y":318}}},{"id":"3434e4a0-e2c1-4c3a-9f52-81ae81a852e2","type":"SetQueue","branches":[{"condition":"Success","transition":"919982d6-3066-49e5-afe5-619896781245"},{"condition":"Error","transition":"919982d6-3066-49e5-afe5-619896781245"}],"parameters":[{"name":"Queue","value":"arn:aws:connect:us-west-2:359844746047:instance/95e795d6-c32d-4430-932b-1ded68353e50/queue/ff94aae2-aad3-4618-bbda-9af50bbb7b5a","namespace":null,"resourceName":"BasicQueue"}],"metadata":{"position":{"x":691,"y":320},"useDynamic":false,"queue":{"id":"arn:aws:connect:us-west-2:359844746047:instance/95e795d6-c32d-4430-932b-1ded68353e50/queue/ff94aae2-aad3-4618-bbda-9af50bbb7b5a","text":"BasicQueue"}}},{"id":"aa21389d-0252-465c-80ec-2c9ea9a83b19","type":"PlayPrompt","branches":[{"condition":"Success","transition":"99458f47-6941-48ce-9b90-fdf184759b22"}],"parameters":[{"name":"Text","value":"An error occurred with the KVS trigger lambda function.","namespace":null},{"name":"TextToSpeechType","value":"text"}],"metadata":{"position":{"x":729,"y":688},"useDynamic":false}},{"id":"97a964a7-5dd2-4c82-b21f-173b209be8a7","type":"InvokeExternalResource","branches":[{"condition":"Success","transition":"3434e4a0-e2c1-4c3a-9f52-81ae81a852e2"},{"condition":"Error","transition":"aa21389d-0252-465c-80ec-2c9ea9a83b19"}],"parameters":[{"name":"FunctionArn","value":"${lambdaTriggerArn}","namespace":null},{"name":"TimeLimit","value":"8"}],"metadata":{"position":{"x":393,"y":469},"dynamicMetadata":{},"useDynamic":false},"target":"Lambda"},{"id":"99458f47-6941-48ce-9b90-fdf184759b22","type":"Disconnect","branches":[],"parameters":[],"metadata":{"position":{"x":730,"y":937}}},{"id":"abe8c2b7-f002-41b1-8e9e-374ff32c2351","type":"InvokeExternalResource","branches":[{"condition":"Success","transition":"e7825b58-a9db-4935-9f83-e67a564176e8"},{"condition":"Error","transition":"e7825b58-a9db-4935-9f83-e67a564176e8"}],"parameters":[{"name":"FunctionArn","value":"${lambdaInitArn}","namespace":null},{"name":"TimeLimit","value":"8"}],"metadata":{"position":{"x":386,"y":221},"dynamicMetadata":{},"useDynamic":false},"target":"Lambda"},{"id":"e7825b58-a9db-4935-9f83-e67a564176e8","type":"SetAttributes","branches":[{"condition":"Success","transition":"97a964a7-5dd2-4c82-b21f-173b209be8a7"},{"condition":"Error","transition":"99458f47-6941-48ce-9b90-fdf184759b22"}],"parameters":[{"name":"Attribute","value":"true","key":"transcribeCall","namespace":null},{"name":"Attribute","value":"false","key":"saveCallRecording","namespace":null},{"name":"Attribute","value":"aid","key":"aid","namespace":"External"},{"name":"Attribute","value":"sak","key":"sak","namespace":"External"},{"name":"Attribute","value":"sst","key":"sst","namespace":"External"},{"name":"Attribute","value":"en-US","key":"languageCode","namespace":null}],"metadata":{"position":{"x":161,"y":468}}}],"version":"1","type":"contactFlow","start":"856dd865-e5a0-49c6-aacc-55fe53c38a22","metadata":{"entryPointPosition":{"x":15,"y":20},"snapToGrid":false,"name":"kvsStreamingTranscribeFlow","description":null,"type":"contactFlow","status":"published","hash":"a07d26212ba8149317ebece6318cbc4e6b7a970bffe1c0b4dc59eb491662c0d9"}}`;
    uploadFlowToS3('kvsStreamingTranscribeFlow', mainFlow, bucketName, S3, callback);
}

createContactFlow.handler = function(event, context) {
    console.log(JSON.stringify(event, null, '  '));

    if (event.RequestType == 'Delete') {
        return sendResponse(event, context, "SUCCESS");
    }

    createContactFlow(event.ResourceProperties, function(err, result) {
        var status = err ? 'FAILED' : 'SUCCESS';
        return sendResponse(event, context, status, result, err);
    });
};

function getReason(err) {
    if (err)
        return err.message;
    else
        return '';
}

function uploadFlowToS3(name, body, bucketName, S3, callback) {
    S3.putObject({
        Bucket: bucketName,
        Key: name,
        Body:body
    }, function(err, data) {

        if (err)
            return callback(err);

        return callback(null, "SUCCESS");
    });
}


function sendResponse(event, context, status, data, err) {
    var responseBody = {
        StackId: event.StackId,
        RequestId: event.RequestId,
        LogicalResourceId: event.LogicalResourceId,
        PhysicalResourceId: context.logStreamName,
        Status: status,
        Reason: getReason(err) + " See details in CloudWatch Log: " + context.logStreamName,

    };

    console.log("RESPONSE:\n", responseBody);
    var json = JSON.stringify(responseBody);

    var https = require("https");
    var url = require("url");

    var parsedUrl = url.parse(event.ResponseURL);
    var options = {
        hostname: parsedUrl.hostname,
        port: 443,
        path: parsedUrl.path,
        method: "PUT",
        headers: {
            "content-type": "",
            "content-length": json.length
        }
    };

    var request = https.request(options, function(response) {
        console.log("STATUS: " + response.statusCode);
        console.log("HEADERS: " + JSON.stringify(response.headers));
        context.done(null, data);
    });

    request.on("error", function(error) {
        console.log("sendResponse Error:\n", error);
        context.done(error);
    });

    request.on("end", function() {
        console.log("end");
    });
    request.write(json);
    request.end();
}

module.exports = createContactFlow;

if(require.main === module) {
    console.log("called directly");
    if (process.argv.length < 3)
        usageExit();
    try {
        var data = JSON.parse(process.argv[2]);
    } catch (error) {
        console.error('Invalid JSON', error);
        usageExit();
    }
    createContactFlow(data, function(err, res) {
        console.log("Result", err, res);
    });
}

function usageExit() {
    var path = require('path');
    console.error('Usage: '  + path.basename(process.argv[1]) + ' json-array');
    process.exit(1);
}