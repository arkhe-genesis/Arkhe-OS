// src/main/java/com/arkhe/banking/controller/CreditScoringController.java
package com.arkhe.banking.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;

@RestController
@RequestMapping("/api/v1/credit")
@ComplianceVerified(jurisdictions = {Jurisdiction.BCB, Jurisdiction.BASILEIA})
public class CreditScoringController {

    @Autowired
    private ComplianceValidator complianceValidator;

    @Autowired
    private ZincPlusProver zincProver;

    @PostMapping("/score")
    @PreAuthorize("hasRole('CREDIT_OFFICER')")
    public ResponseEntity<ScoringResponse> calculateScore(
            @RequestBody @RegulatoryValidated CreditApplication application,
            @RequestHeader("X-Regulatory-Context") String regulatoryContext) {

        // 1. Parse da aplicação para LFIR (simulado)
        LFIRGraph applicationLFIR = lfirParser.parseCreditApplication(application);

        // 2. Verificar compliance contra predicados BCB
        ComplianceVerificationResult verification = complianceValidator.verifyArtifact(
            application.getApplicationId(),
            applicationLFIR,
            List.of("credit_fairness_bcb", "capital_adequacy_basel"),
            List.of(Jurisdiction.BCB, Jurisdiction.BASILEIA),
            true  // Generate ZK proof
        );

        // 3. Se não compliant, retornar erro detalhado
        if (!verification.is_fully_compliant()) {
            return ResponseEntity.badRequest()
                .body(ScoringResponse.error(
                    "Compliance verification failed",
                    verification.to_regulatory_report()
                ));
        }

        // 4. Calcular score de crédito (lógica de negócio)
        CreditScore score = creditScoringService.calculate(application);

        // 5. Registrar auditoria com proof ZK
        AuditEntry auditEntry = new AuditEntry(
            application.getApplicationId(),
            "CREDIT_SCORE_CALCULATED",
            verification.getZk_proof_hash(),
            verification.getCoherence_score()
        );
        auditLogService.log(auditEntry);

        // 6. Retornar resposta com metadata de compliance
        return ResponseEntity.ok(ScoringResponse.success(score)
            .withComplianceMetadata(
                verification.getVerification_id(),
                verification.getZk_proof_hash(),
                verification.getCoherence_score()
            ));
    }
}
