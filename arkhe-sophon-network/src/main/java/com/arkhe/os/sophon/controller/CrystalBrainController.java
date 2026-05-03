package com.arkhe.os.sophon.controller;

import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/crystal")
public class CrystalBrainController {

    @PostMapping("/optimize")
    public Mono<String> runHomeostasis(
            @RequestParam(defaultValue = "0.75") double initialKappa,
            @RequestParam(defaultValue = "0.02") double initialLambda,
            @RequestParam(defaultValue = "8") int epochs) {
        return Mono.just("Optimization Initiated");
    }

    @GetMapping("/regime")
    public Mono<String> getRegime() {
        return Mono.just("CAPTURE");
    }

    @PostMapping("/proof/generate")
    public Mono<String> generateProof(
            @RequestParam(defaultValue = "80") int securityBits) {
        return Mono.just("Proof Generated");
    }
}
