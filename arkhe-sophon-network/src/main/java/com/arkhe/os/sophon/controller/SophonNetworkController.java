package com.arkhe.os.sophon.controller;

import com.arkhe.os.sophon.model.*;
import com.arkhe.os.sophon.service.CoherenceRoutingService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/api/v1/sophon")
@RequiredArgsConstructor
public class SophonNetworkController {

    private final CoherenceRoutingService routingService;

    @PostMapping("/send")
    public Mono<SophonPacket> sendPacket(
            @RequestBody SophonPacket packet,
            @RequestParam(defaultValue = "0.85") double coherenceThreshold) {
        return routingService.sendPacket(packet, coherenceThreshold);
    }

    @GetMapping(value = "/metrics/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<CoherenceMetric> streamMetrics() {
        return routingService.streamCoherenceMetrics();
    }
}
