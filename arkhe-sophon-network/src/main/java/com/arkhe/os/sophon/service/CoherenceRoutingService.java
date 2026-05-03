package com.arkhe.os.sophon.service;

import com.arkhe.os.sophon.model.*;
import com.arkhe.os.sophon.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Flux;

import java.time.Instant;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class CoherenceRoutingService {

    private final CoherenceMetricRepository metricRepository;
    private final SophonPacketRepository packetRepository;
    private final BraidCircuitRepository circuitRepository;

    public Mono<List<String>> routeByCoherenceGeodesic(
            String sourceAddress,
            String destAddress,
            double coherenceThreshold) {

        return Mono.just(List.of(sourceAddress, destAddress));
    }

    @Transactional
    public Mono<SophonPacket> sendPacket(SophonPacket packet, double coherenceThreshold) {
        packet.setTimestamp(Instant.now());
        packet.setPayloadIntegrityHash("dummy_hash");
        SophonPacket savedPacket = packetRepository.save(packet);
        return Mono.just(savedPacket);
    }

    public Flux<CoherenceMetric> streamCoherenceMetrics() {
        return Flux.fromIterable(packetRepository.findAll())
            .map(packet -> CoherenceMetric.builder()
                .nodeId(packet.getSourceHash())
                .coherenceDistance(packet.getPhiManifestation())
                .deliveryRate(0.95)
                .timestamp(packet.getTimestamp())
                .build()
            );
    }
}
