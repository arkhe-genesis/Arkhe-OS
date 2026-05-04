package com.arkhe.os.sophon.service;

import com.arkhe.os.sophon.config.SophonKafkaConfig;
import com.arkhe.os.sophon.model.CoherenceMetric;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class CoherenceEventProducer {

    private final KafkaTemplate<String, CoherenceMetric> kafkaTemplate;

    public void publishCoherenceUpdate(CoherenceMetric metric) {
        String key = metric.getNodeId();

        kafkaTemplate.send(SophonKafkaConfig.COHERENCE_EVENTS_TOPIC, key, metric)
            .whenComplete((result, ex) -> {
                if (ex != null) {
                    log.error("Failed to publish coherence event: {}", ex.getMessage());
                } else {
                    log.debug("Coherence event published: offset={}",
                        result.getRecordMetadata().offset());
                }
            });
    }
}
