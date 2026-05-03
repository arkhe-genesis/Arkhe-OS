package com.arkhe.os.sophon.model;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "coherence_metrics", indexes = {
    @Index(name = "idx_node_timestamp", columnList = "nodeId, timestamp")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CoherenceMetric {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 64)
    private String nodeId;

    @Column(nullable = false)
    private Double coherenceDistance;

    @Column(nullable = false)
    private Double deliveryRate;

    @Column(nullable = false)
    private Double cacheHitRate;

    @Column(nullable = false)
    private Double p99LatencyMs;

    @Column(nullable = false)
    private Double bitErrorRate;

    @Column(nullable = false)
    private Double coherenceEstimationError;

    @Column(nullable = false)
    private Instant timestamp;
}
