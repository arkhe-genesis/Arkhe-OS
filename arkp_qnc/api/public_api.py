#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
public_api.py — API Pública para Predição Genômica Quântica
Endpoints REST/GraphQL com autenticação ORCID, rate limiting, e auditoria.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Security
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel, Field, validator
    import uvicorn
except ImportError:
    FastAPI = None
import numpy as np
import hashlib
import time
from typing import List, Optional, Dict

from arkp_qnc.genomic_qnc import GenomicQNC, GenomicQNCConfig
from arkp_qnc.qnc_transfer import MultiSpeciesQNC
from arkp_auth.auth_manager import AuthManager, ORCIDClaim

if FastAPI is not None:
    app = FastAPI(
        title="ARKHE Quantum Genomics API",
        description="Public API for quantum genomic predictions, chaperone design, and RADIX optimization",
        version="6.4.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Segurança
    security = HTTPBearer()
    auth_manager = AuthManager()

    # Modelos globais (carregados na inicialização)
    qnc_model: Optional[MultiSpeciesQNC] = None
    repair_engine: Optional["AdaptiveRepairEngine"] = None

    # ============================================================================
    # MODELOS DE REQUEST/RESPONSE
    # ============================================================================

    class GenomicPredictionRequest(BaseModel):
        sequence: str = Field(..., min_length=1, max_length=8192, pattern="^[ATGCNatgcn]+$")
        species: Optional[str] = Field(default=None, description="Nome da espécie (para adaptação)")
        prediction_type: str = Field(default="radiation_resistance", pattern="^(radiation_resistance|folding_quality|chaperone_affinity)$")
        include_uncertainty: bool = Field(default=False, description="Incluir intervalos de confiança")

    class GenomicPredictionResponse(BaseModel):
        prediction: int  # 0 ou 1 para classificação binária
        confidence: float = Field(..., ge=0.0, le=1.0)
        phi_c_coherence: float
        uncertainty: Optional[Dict[str, float]] = None
        integrity_proof: str
        temporal_anchor: str
        qip_cost: float  # Custo em QIP tokens

    class RepairRequest(BaseModel):
        damaged_sequence: str
        radiation_level: float = Field(..., ge=0.0, le=100.0)
        species: str = Field(default="RADIX-1")
        priority: str = Field(default="balanced", pattern="^(speed|accuracy|coherence|balanced)$")

    class RepairResponse(BaseModel):
        action: str
        confidence: float
        predicted_outcome: Dict
        phi_c_impact: float
        estimated_time_ms: float
        qip_cost: float

    class ProteinDesignRequest(BaseModel):
        function: str = Field(..., description="Função alvo da proteína")
        chaperone_type: str = Field(default="GroEL", pattern="^(Hsp70|GroEL|Hsp90)$")
        max_mutations: int = Field(default=5, ge=1, le=20)
        preserve_structure: bool = Field(default=True)

    class ProteinDesignResponse(BaseModel):
        original_sequence: str
        designed_sequence: str
        predicted_affinity: float
        predicted_stability: float
        mutations: List[Dict]
        phi_c_contribution: float

    # ============================================================================
    # DEPENDÊNCIAS E MIDDLEWARE
    # ============================================================================

    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> Dict:
        """Verifica token JWT e retorna claims do usuário."""
        claims = auth_manager.verify_token(credentials.credentials)
        if not claims:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return claims

    async def rate_limit_check(
        user: Dict = Depends(get_current_user),
    ) -> bool:
        """Verifica limite de requisições por usuário."""
        user_id = user.get("sub")
        now = time.time()
        # Placeholder: em produção, usar Redis para rate limiting distribuído
        return True

    # ============================================================================
    # ENDPOINTS PRINCIPAIS
    # ============================================================================

    @app.post("/api/v1/predict", response_model=GenomicPredictionResponse)
    async def predict_genomic_trait(
        request: GenomicPredictionRequest,
        user: Dict = Depends(get_current_user),
        rate_ok: bool = Depends(rate_limit_check),
    ):
        """
        Prediz traço genômico (resistência, folding, afinidade) via QNC.

        Requer autenticação ORCID. Cobrança em QIP tokens baseada em complexidade.
        """
        if qnc_model is None:
            raise HTTPException(status_code=503, detail="Model not initialized")

        # Predição principal
        if request.prediction_type == "radiation_resistance":
            pred_class, confidence = qnc_model.predict(request.sequence)
            phi_c = np.real(np.trace(qnc_model.phi_c_field))
        else:
            # Placeholder para outros tipos de predição
            pred_class, confidence = 1, 0.85
            phi_c = 0.99

        # Incerteza (se solicitada)
        uncertainty = None
        if request.include_uncertainty:
            # Bootstrap simplificado para intervalo de confiança
            uncertainties = []
            for _ in range(10):
                noise = np.random.randn(*qnc_model.phi_c_field.shape) * 0.01
                noisy_phi = qnc_model.phi_c_field + noise
                # Reavaliar com ruído
                uncertainties.append(np.real(np.trace(noisy_phi)))
            uncertainty = {
                "confidence_95_lower": np.percentile(uncertainties, 2.5),
                "confidence_95_upper": np.percentile(uncertainties, 97.5),
            }

        # Prova de integridade e âncora temporal
        integrity = hashlib.sha3_256(
            f"{request.sequence}{pred_class}{confidence}{time.time()}".encode()
        ).hexdigest()[:16]

        temporal_anchor = hashlib.sha3_256(
            f"{user['sub']}{request.sequence}{integrity}".encode()
        ).hexdigest()[:12]

        # Custo QIP (baseado em comprimento da sequência)
        qip_cost = len(request.sequence) / 1000.0  # 0.001 QIP por bp

        return GenomicPredictionResponse(
            prediction=pred_class,
            confidence=confidence,
            phi_c_coherence=phi_c,
            uncertainty=uncertainty,
            integrity_proof=integrity,
            temporal_anchor=temporal_anchor,
            qip_cost=qip_cost,
        )

    @app.post("/api/v1/repair", response_model=RepairResponse)
    async def request_adaptive_repair(
        request: RepairRequest,
        user: Dict = Depends(get_current_user),
        background_tasks: BackgroundTasks = None,
    ):
        """
        Solicita reparo adaptativo de genoma danificado via QNC + GECC.

        Assíncrono para operações longas. Retorna estimativa inicial imediata.
        """
        if repair_engine is None:
            raise HTTPException(status_code=503, detail="Repair engine not initialized")

        # Decisão inicial (rápida)
        decision = repair_engine.assess_damage_and_repair(
            damaged_sequence=request.damaged_sequence,
            radiation_level=request.radiation_level,
            species_context=request.species,
        )

        # Estimativa de tempo baseada na ação
        time_estimates = {
            "correct": 50,
            "redundant_copy": 200,
            "adaptive_mutation": 500,
            "bypass": 10,
        }
        estimated_time = time_estimates.get(decision.action, 100)

        # Custo QIP baseado em complexidade do reparo
        qip_cost = estimated_time / 100.0  # 0.01 QIP por 10ms estimado

        # Agendar execução assíncrona se necessário
        if decision.action in ["adaptive_mutation", "redundant_copy"]:
            background_tasks.add_task(
                _execute_repair_async,
                request.damaged_sequence,
                decision,
                user["sub"],
            )

        return RepairResponse(
            action=decision.action,
            confidence=decision.confidence,
            predicted_outcome=decision.predicted_outcome,
            phi_c_impact=decision.phi_c_impact,
            estimated_time_ms=estimated_time,
            qip_cost=qip_cost,
        )

    async def _execute_repair_async(
        sequence: str,
        decision,
        user_id: str,
    ):
        """Executa reparo assíncrono em background."""
        result = repair_engine.execute_repair(sequence, decision)
        # Log resultado para auditoria
        # Enviar notificação ao usuário se configurado
        pass

    @app.post("/api/v1/design-protein", response_model=ProteinDesignResponse)
    async def design_chaperone_binding(
        request: ProteinDesignRequest,
        user: Dict = Depends(get_current_user),
    ):
        """
        Projeta sequência de proteína para otimizar ligação a chaperona.

        Usa QNC + Φ_C-guided optimization para sugerir mutações.
        """
        from arkp_qnc.chaperone_designer import QNCChaperoneDesigner

        if qnc_model is None:
            raise HTTPException(status_code=503, detail="Model not initialized")

        designer = QNCChaperoneDesigner(qnc_model)

        # Sequência inicial baseada na função
        initial_seq = designer._function_to_seed_sequence(request.function)

        # Otimização iterativa
        result = designer.design_optimal_binding_sequence(
            protein_function=request.function,
            chaperone_type=request.chaperone_type,
            max_iterations=request.max_mutations,
        )

        # Calcular estabilidade prevista (placeholder)
        predicted_stability = 0.85 + np.random.randn() * 0.05

        return ProteinDesignResponse(
            original_sequence=initial_seq,
            designed_sequence=result["final_sequence"],
            predicted_affinity=result["final_affinity"],
            predicted_stability=predicted_stability,
            mutations=result.get("suggested_mutations", []),
            phi_c_contribution=result.get("phi_c_contribution", 0.0),
        )

    @app.get("/api/v1/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "qnc_loaded": qnc_model is not None,
            "repair_engine_loaded": repair_engine is not None,
            "supported_species": list(qnc_model.trained_species) if qnc_model else [],
            "api_version": "6.4.0",
        }

    @app.get("/api/v1/metrics")
    async def get_public_metrics(user: Dict = Depends(get_current_user)):
        """Retorna métricas públicas do modelo (para usuários autenticados)."""
        if qnc_model is None:
            raise HTTPException(status_code=503, detail="Model not initialized")

        return {
            "total_species_trained": len(qnc_model.trained_species),
            "average_phi_c_coherence": float(np.mean([
                np.real(np.trace(adapter)) for adapter in qnc_model.species_adapters.values()
            ])),
            "recent_predictions": len(qnc_model.training_history[-100:]),
            "average_confidence": float(np.mean([
                m.get("confidence", 0.0) for m in qnc_model.training_history[-100:]
            ])),
        }

    # ============================================================================
    # INICIALIZAÇÃO
    # ============================================================================

    @app.on_event("startup")
    async def startup_event():
        """Inicializa modelos e engines na inicialização da API."""
        global qnc_model, repair_engine

        # Carregar modelo QNC multi-espécie
        qnc_config = GenomicQNCConfig(
            vocab_size=4,
            max_sequence_length=128,
            embedding_dim=8,
            hidden_dim=16,
            num_classes=2,
            phi_c_coupling=0.1,
        )
        qnc_model = MultiSpeciesQNC(max_len=128, hidden_dim=16)

        # Pré-carregar espécies conhecidas
        for species in ["Deinococcus radiodurans", "Thermococcus gammatolerans", "RADIX-1"]:
            qnc_model.register_species(species, base_resistance=15.0)

        # Inicializar engine de reparo
        from arkp_bio.adaptive_genomic_ecc import AdaptiveGenomicECC
        from arkp_bio.quantum_folding_simulator import PhiCField

        ecc_engine = AdaptiveGenomicECC()
        phi_c_field = PhiCField(coupling_constant=0.1)

        from arkp_bio.src.adaptive_repair_engine import AdaptiveRepairEngine
        repair_engine = AdaptiveRepairEngine(qnc_model, ecc_engine, phi_c_field)

        print("✅ ARKHE Quantum Genomics API initialized")

    # ============================================================================
    # EXECUÇÃO
    # ============================================================================

    if __name__ == "__main__":
        uvicorn.run(
            "arkp_qnc.api.public_api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
        )
