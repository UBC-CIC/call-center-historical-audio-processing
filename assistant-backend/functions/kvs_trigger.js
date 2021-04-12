/**********************************************************************************************************************
 *  Code mostly taken from https://github.com/amazon-connect/amazon-connect-realtime-transcription                                                                                                 *
 **********************************************************************************************************************/

'use strict';
const AWS = require('aws-sdk');
const lambda = new AWS.Lambda();

/**
 * Lambda function entry point, takes the audio data from the Kinesis Video stream resource
 * and passes that as a parameter to invoke another Lambda function, the transcription Function
 * @param event
 * @param context
 * @param callback
 */
exports.handler = (event, context, callback) => {

    console.log("Received event from Amazon Connect " + JSON.stringify(event));

    let payload = "";

    if (event.eventType) {
        payload ={
            inputFileName: "keepWarm.wav",
            connectContactId: "12b87d2b-keepWarm",
            transcriptionEnabled: "false"
        };
    } else {
        payload = {
            streamARN: event.Details.ContactData.MediaStreams.Customer.Audio.StreamARN,
            startFragmentNum: event.Details.ContactData.MediaStreams.Customer.Audio.StartFragmentNumber,
            connectContactId: event.Details.ContactData.ContactId,
            transcriptionEnabled: event.Details.ContactData.Attributes.transcribeCall === "true" ? true : false,
            saveCallRecording: event.Details.ContactData.Attributes.saveCallRecording === "false" ? false : true,
            languageCode: event.Details.ContactData.Attributes.languageCode === "es-US" ? "es-US" : "en-US",
            // These default to true for backwards compatability purposes
            streamAudioFromCustomer: event.Details.ContactData.Attributes.streamAudioFromCustomer === "false" ? false : true,
            streamAudioToCustomer: event.Details.ContactData.Attributes.streamAudioToCustomer === "false" ? false : true
        };
    }

    console.log("Trigger event passed to transcriberFunction" + JSON.stringify(payload));

    const params = {
        // not passing in a ClientContext
        'FunctionName': process.env.transcriptionFunction,
        // InvocationType is RequestResponse by default
        // LogType is not set so we won't get the last 4K of logs from the invoked function
        // Qualifier is not set so we use $LATEST
        'InvokeArgs': JSON.stringify(payload)
    };

    lambda.invokeAsync(params, function(err, data) {
        if (err) {
            throw (err);
        } else {
            console.log(JSON.stringify(data));
            if (callback)
                callback(null, buildResponse());
            else
                console.log('nothing to callback so letting it go');
        }
    });

    callback(null, buildResponse());
};

/**
 * Response function for the lambda handler that is passed as a callback
 */
function buildResponse() {
    return {
        // we always return "Success" for now
        lambdaResult:"Success"
    };
}
