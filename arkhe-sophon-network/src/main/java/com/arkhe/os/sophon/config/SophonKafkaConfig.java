package com.arkhe.os.sophon.config;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
public class SophonKafkaConfig {

    public static final String COHERENCE_EVENTS_TOPIC = "arkhe.coherence.events";
    public static final String PROOF_REQUESTS_TOPIC = "arkhe.proof.requests";
    public static final String ROUTING_UPDATES_TOPIC = "arkhe.routing.updates";
    public static final String OCTRA_SUBMISSIONS_TOPIC = "arkhe.octra.submissions";

    @Bean
    public NewTopic coherenceEventsTopic() {
        return TopicBuilder.name(COHERENCE_EVENTS_TOPIC)
            .partitions(12) // 12 partições — uma por camada da treliça torcional
            .replicas(1)
            .config(org.apache.kafka.common.config.TopicConfig.RETENTION_MS_CONFIG, "604800000") // 7 dias
            .build();
    }

    @Bean
    public NewTopic proofRequestsTopic() {
        return TopicBuilder.name(PROOF_REQUESTS_TOPIC)
            .partitions(6)
            .replicas(1)
            .build();
    }
}
