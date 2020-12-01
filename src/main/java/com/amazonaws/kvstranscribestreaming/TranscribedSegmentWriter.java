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
 * Code largely modified and based from https://github.com/amazon-connect/amazon-connect-realtime-transcription 
 *
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

                double startTime = result.startTime();

                // concatenate transcript result over time in DynamoDB item if it exists
                if (existingDdbItem != null) {
                    String currentTranscript = existingDdbItem.getString("Transcript");
                    transcript = currentTranscript.concat(" " + transcript);

                    startTime = existingDdbItem.getDouble("StartTime");
                }

                Instant now = Instant.now();
                ddbItem = new Item()
                        .withKeyComponent("ContactId", contactId)
                        .withDouble("StartTime", startTime)
                        .withDouble("EndTime", result.endTime())
                        .withString("SegmentId", result.resultId())
                        .withString("Transcript", transcript)
                        .withBoolean("IsPartial", result.isPartial())
                        // LoggedOn is an ISO-8601 string representation of when the entry was created
                        .withString("LoggedOn", now.toString())
                        // expire entries after 6 hours of creation/update
                        .withDouble("ExpiresOn", now.plusSeconds(6 * 3600).getEpochSecond());

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
