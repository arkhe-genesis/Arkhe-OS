#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qnc_api.py — API HTTP para Substrato 6176: Quantum Neural Coding
Endpoints para predição genômica, design de chaperonas, e análise Φ_C.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np
import hashlib

from arkp_qnc.src.genomic_qnc import GenomicQNC, GenomicQNCConfig
from arkp_qnc.src.chaperone_designer import QNCChaperoneDesigner
from arkp_qnc.src.quantum_layers import fidelity

app = FastAPI(
    title="ARKHE QNC API",
    description="Quantum Neural Coding for Genomic Intelligence",
    version="6.3.0",
)

# Modelo global (carregado na inicialização)
qnc_model: Optional[GenomicQNC] = None
chaperone_designer: Optional[QNCChaperoneDesigner] = None

class SequenceRequest(BaseModel):
    sequence: str = Field(..., min_length=1, max_length=512, pattern="^[ATGCatgc]+$")
    chaperone_type: Optional[str] = Field(default="GroEL", pattern="^(Hsp70|GroEL)$")

class PredictionResponse(BaseModel):
    predicted_class: int
    confidence: float
    phi_c_coherence: float
    integrity_proof: str

class ChaperoneDesignRequest(BaseModel):
    protein_sequence: str
    chaperone_type: str = "GroEL"
    target_affinity: float = Field(0.8, ge=0.0, le=1.0)
    max_mutations: int = Field(3, ge=1, le=10)

class ChaperoneDesignResponse(BaseModel):
    original_sequence: str
    suggested_mutations: List[dict]
    predicted_affinity_before: float
    predicted_affinity_after: float
    confidence: float

@app.on_event("startup")
async def startup_event():
    """Inicializa modelo QNC ao iniciar API."""
    global qnc_model, chaperone_designer

    # Carregar modelo pré-treinado ou inicializar novo
    config = GenomicQNCConfig(
        vocab_size=4,
        max_sequence_length=128,
        embedding_dim=8,
        hidden_dim=16,
        num_classes=2,
        phi_c_coupling=0.1,
    )
    qnc_model = GenomicQNC(config)
    chaperone_designer = QNCChaperoneDesigner(qnc_model)

    # Em produção: carregar checkpoint treinado
    # qnc_model = GenomicQNC.load_checkpoint("checkpoints/qnc_radix1_v1.pkl")

@app.post("/api/v1/qnc/predict", response_model=PredictionResponse)
async def predict_radiation_resistance(req: SequenceRequest):
    """
    Prediz resistência a radiação a partir de sequência de DNA.

    Retorna classe (0=sensível, 1=resistente) e confiança.
    """
    if qnc_model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

    pred_class, confidence = qnc_model.predict(req.sequence.upper())
    phi_c_coherence = fidelity(
        qnc_model.phi_c_field,
        np.eye(qnc_model.config.hidden_dim) / qnc_model.config.hidden_dim
    )

    return PredictionResponse(
        predicted_class=pred_class,
        confidence=confidence,
        phi_c_coherence=phi_c_coherence,
        integrity_proof=hashlib.sha3_256(
            f"{req.sequence}{pred_class}{confidence}".encode()
        ).hexdigest()[:16],
    )

@app.post("/api/v1/qnc/design-chaperone", response_model=ChaperoneDesignResponse)
async def design_chaperone_binding(req: ChaperoneDesignRequest):
    """
    Sugere mutações para aumentar afinidade de ligação a chaperona.
    """
    if chaperone_designer is None:
        raise HTTPException(status_code=503, detail="Designer not initialized")

    result = chaperone_designer.suggest_mutations(
        protein_sequence=req.protein_sequence,
        chaperone_type=req.chaperone_type,
        target_affinity=req.target_affinity,
        max_mutations=req.max_mutations,
    )

    return ChaperoneDesignResponse(
        original_sequence=result.original_sequence,
        suggested_mutations=result.suggested_mutations,
        predicted_affinity_before=result.predicted_affinity_before,
        predicted_affinity_after=result.predicted_affinity_after,
        confidence=result.confidence,
    )

@app.get("/api/v1/qnc/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": qnc_model is not None,
        "phi_c_coherence": float(qnc_model.phi_c_field.trace().real / qnc_model.phi_c_field.shape[0]) if qnc_model else None,
    }

@app.get("/api/v1/qnc/metrics")
async def get_training_metrics():
    """Retorna métricas de treinamento do modelo."""
    if qnc_model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

    return {
        "training_steps": len(qnc_model.training_history),
        "recent_losses": [m['loss'] for m in qnc_model.training_history[-10:]],
        "phi_c_coherence": float(qnc_model.phi_c_field.trace().real / qnc_model.phi_c_field.shape[0]),
    }
