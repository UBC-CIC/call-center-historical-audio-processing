package com.amazonaws.kvstranscribestreaming;

import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Item;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.amazonaws.services.dynamodbv2.document.UpdateItemOutcome;
import com.amazonaws.services.dynamodbv2.document.spec.GetItemSpec;
import com.amazonaws.services.dynamodbv2.document.spec.UpdateItemSpec;
import com.amazonaws.services.dynamodbv2.document.utils.NameMap;
import com.amazonaws.services.dynamodbv2.document.utils.ValueMap;
import com.amazonaws.services.dynamodbv2.model.ReturnValue;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awssdk.services.transcribestreaming.model.Result;
import software.amazon.awssdk.services.transcribestreaming.model.TranscriptEvent;

import java.text.NumberFormat;
import java.time.Instant;
import java.util.List;

/**
 * TranscribedSegmentWriter writes the transcript segments to DynamoDB
 *
 * <p>Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.</p>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this
 * software and associated documentation files (the "Software"), to deal in the Software
 * without restriction, including without limitation the rights to use, copy, modify,
 * merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so.
 * <p>
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 * PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
public class TranscribedSegmentWriter {

    private String contactId;
    private DynamoDB ddbClient;
    private Boolean consoleLogTranscriptFlag;

    private static final Logger logger = LoggerFactory.getLogger(TranscribedSegmentWriter.class);

    public TranscribedSegmentWriter(String contactId, DynamoDB ddbClient, Boolean consoleLogTranscriptFlag) {

        this.contactId = Validate.notNull(contactId);
        this.ddbClient = Validate.notNull(ddbClient);
        this.consoleLogTranscriptFlag = Validate.notNull(consoleLogTranscriptFlag);
    }

    public String getContactId() {
        return this.contactId;
    }

    public DynamoDB getDdbClient() {
        return this.ddbClient;
    }

    public void writeToDynamoDB(TranscriptEvent transcriptEvent, String tableName) {
        logger.info("table name: " + tableName);
        logger.info("Transcription event: " + transcriptEvent.transcript().toString());

        List<Result> results = transcriptEvent.transcript().results();

        if (results.size() > 0) {

            Result result = results.get(0);

            // No partial results will be written to DynamoDB
            if (!result.isPartial()) {
                try {
                    Item ddbItem = toDynamoDbItem(result, tableName);
                    if (ddbItem != null) {
                        getDdbClient().getTable(tableName).putItem(ddbItem);
                        logger.info("PutItem succeeded.");
                    }
                } catch (Exception e) {
                    logger.error(e.getMessage());
                }
            }
        }
    }

    private Item toDynamoDbItem(Result result, String tableName) {

        String contactId = this.getContactId();
        Item ddbItem = null;

        NumberFormat nf = NumberFormat.getInstance();
        nf.setMinimumFractionDigits(3);
        nf.setMaximumFractionDigits(3);

        String transcript = result.alternatives().get(0).transcript();

        GetItemSpec getSpec = new GetItemSpec().withPrimaryKey("ContactId", contactId);
        Item existingDdbItem = getDdbClient().getTable(tableName).getItem(getSpec);
        
        logger.info("GetItem succeeded: " + existingDdbItem);

        if (result.alternatives().size() > 0) {
            if (!transcript.isEmpty()) {

                // concatenate transcript result over time in DynamoDB item if it exists
                if (existingDdbItem != null) {
                    String currentTranscript = existingDdbItem.getString("Transcript");
                    transcript = currentTranscript.concat(" " + transcript);
                }

                Instant now = Instant.now();
                ddbItem = new Item()
                        .withKeyComponent("ContactId", contactId)
                        .withDouble("StartTime", result.startTime())
                        .withDouble("EndTime", result.endTime())
                        .withString("SegmentId", result.resultId())
                        .withString("Transcript", transcript)
                        .withBoolean("IsPartial", result.isPartial())
                        // LoggedOn is an ISO-8601 string representation of when the entry was created
                        .withString("LoggedOn", now.toString())
                        // expire entries after 6 hours of creation/update
                        .withDouble("ExpiresOn", now.plusMillis(6 * 3600).toEpochMilli());

                if (consoleLogTranscriptFlag) {
                    logger.info(String.format("Thread %s %d: [%s, %s] - %s",
                            Thread.currentThread().getName(),
                            System.currentTimeMillis(),
                            nf.format(result.startTime()),
                            nf.format(result.endTime()),
                            result.alternatives().get(0).transcript()));
                }
            }
        }

        return ddbItem;
    }
}
