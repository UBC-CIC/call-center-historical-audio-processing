package com.amazonaws.kvstranscribestreaming;

import com.amazonaws.services.cloudwatch.AmazonCloudWatch;
import com.amazonaws.services.cloudwatch.model.MetricDatum;
import com.amazonaws.services.cloudwatch.model.PutMetricDataRequest;
import com.amazonaws.services.cloudwatch.model.StandardUnit;

import java.time.Instant;
import java.util.Date;

/*
 * <p>Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.</p>
 *
 * Code mostly taken from https://github.com/amazon-connect/amazon-connect-realtime-transcription
 *
 */
public class MetricsUtil {
    /**
     * Class for metrics recording of KinesisVideoStreams in AmazonCloudWatch
     */

    private static String NAMESPACE = "KVSTranscribeStreamingLambda";
    private final AmazonCloudWatch amazonCloudWatch;

    public MetricsUtil(AmazonCloudWatch amazonCloudWatch) {
        this.amazonCloudWatch = amazonCloudWatch;
    }

    public void recordMetric(final String metricName, long value) {
        MetricDatum metricData = new MetricDatum().withMetricName(metricName)
                .withTimestamp(Date.from(Instant.now()))
                .withUnit(StandardUnit.Count)
                .withValue(Double.valueOf(value));

        PutMetricDataRequest metricRequest = new PutMetricDataRequest()
                .withNamespace(NAMESPACE)
                .withMetricData(metricData);

        amazonCloudWatch.putMetricData(metricRequest);
    }
}
