from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import numpy as np
import asyncio
from datetime import datetime, timezone
import logging
import uuid

from skills import (
    simulate_su2_continuous,
    simulate_sl3z_discrete,
    simulate_fibonacci_braid,
    simulate_w_state_coherence,
    simulate_rainbow_coherence,
    simulate_collective_coherence,
    simulate_xenoactualization,
    scan_optimal_measurement_rate,
    optimize_coupling,
    detect_rainbow_peaks,
    detect_peaks,
    synthesize_conclusion,
    optimize_lipus_drug_interval,
    estimate_glymphatic_clearance,
    simulate_phase_oncology,
    simulate_stem_cell_safety,
    calculate_bio_silent_coupling,
    RainbowParams,
    XenoParams,
    KuramotoParams
    lambda2_coherence,
    SynapseKValidator,
    TMSModulator,
    ARChromestheticInterface,
    RainbowParams,
    ArkheMaxTokiIntegration,
    CellularState
)

# Logging configuration
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Archimedes-Ω Agent API",
    description="API for the Archimedes-Ω coherence interrogation agent.",
    version="4.0.0"
    version="2.5.0"
)

# --- Schemas ---

class SU2Request(BaseModel):
    theta_range: List[float] = [0.0, 6.283185307179586]
    num_points: int = Field(1000, ge=10, le=100000)
    thermal_noise: float = Field(0.05, ge=0, le=1)
    temperature: float = Field(310, ge=0)

class SL3ZRequest(BaseModel):
    theta_range: List[float] = [0.0, 6.283185307179586]
    num_points: int = Field(1000, ge=10, le=100000)
    words: List[str] = ["e", "a", "b", "ab", "ba", "aba"]

class WStateRequest(BaseModel):
    nodes: int = Field(3, ge=3, le=10)
    loss_probability: float = Field(0.2, ge=0, le=1)
    theta_range: List[float] = Field([0.0, 6.283185307179586], min_length=2, max_length=2)
    num_points: int = Field(1000, ge=10, le=100000)

class FibonacciRequest(BaseModel):
    dalpha: float = Field(0.0, description="Dipole reorientation (rad). Bound: 0.25° (0.00436 rad)")
    epsilon: float = Field(0.0, description="Helical polarity asymmetry. Bound: 7.07e-3")
    eta: float = Field(0.0, description="Relative phase locking (rad). Bound: 0.41° (0.00715 rad)")
    lambda_param: float = Field(0.0, alias="lambda", description="Leakage amplitude. Bound: 0.01")

class FibonacciResponse(BaseModel):
    braid_fidelity: float
    leakage_probability: float
    gamma5: float
    admissible: bool
    recommendation: str

class CoherenceResponse(BaseModel):
    phases: List[float]
    coherence: List[float]

class PeakDetectionRequest(BaseModel):
    phases: List[float]
    coherence: List[float]
    threshold_multiplier: Optional[float] = 1.2
    min_prominence: Optional[float] = 0.05
    threshold: Optional[float] = 0.3 # For rainbow detection

class PeakInfo(BaseModel):
    phase: float
    phase_degrees: float
    coherence: float
    prominence: Optional[float] = None
    is_resonance: Optional[bool] = None
    fivefold_deviation_rad: Optional[float] = None
    index: Optional[int] = None
    shift_from_base: Optional[float] = None
    peak_type: Optional[str] = None

class PeakDetectionResponse(BaseModel):
    peaks: List[PeakInfo]

class RainbowRequest(BaseModel):
    energy_thz: float = Field(10.0, ge=1.0, le=1000.0)
    num_points: int = Field(1000, ge=10)
    resonance_scale: float = 1.0

class RainbowResponse(BaseModel):
    energy_ev: float
    rainbow_factor: float
    phases: List[float]
    coherence: List[float]
    shifted_peaks: Dict[str, float]
    regime: str
    philosophical_note: str

class RainbowPeakResponse(BaseModel):
    peaks: List[PeakInfo]
    dominant_regime: str
    interpretation: str

class NodeState(BaseModel):
    phase: float
    natural_freq: float
    weight: float = 1.0

class CollectiveCoherenceRequest(BaseModel):
    nodes: List[NodeState]
    coupling_K: float = 1.0
    time_horizon: float = 10.0
    dt: float = 0.01
    fusion_threshold: float = 0.95
    stabilization_time: float = 0.5
    enable_rainbow_resonance: bool = False

class CollectiveCoherenceResponse(BaseModel):
    final_R: float
    final_phase: float
    is_fused: bool
    time_to_fusion: Optional[float]
    trajectory_R: List[float]
    trajectory_phases: List[float]
    resonance_status: Dict[str, Any]
    interpretation: str
    philosophical_note: str

class XenoactualizationRequest(BaseModel):
    coherence_profile: List[float]
    blueprint_complexity: float = Field(..., ge=1.0, le=10.0)
    measurement_rate: float = Field(1.0, ge=0.1, le=100.0)
    tau_field_strength: float = Field(0.5, ge=0.0, le=1.0)
    domain: str = "HYPO"

class XenoactualizationResponse(BaseModel):
    fidelity: float
    zeno_suppression: float
    coherence_factor: float
    complexity_penalty: float
    stability_score: float
    collapse_time_estimate: float
    domain_result: str
    recommendation: str
    philosophical_note: str

class AnalysisRequest(BaseModel):
    data_source: str # simulated or experimental
    su2_params: Optional[SU2Request] = None
    sl3z_params: Optional[SL3ZRequest] = None
    w_state_params: Optional[WStateRequest] = None
    detection_params: Optional[Dict[str, float]] = {"threshold_multiplier": 1.2, "min_prominence": 0.05}
    experimental_data: Optional[Dict[str, List[float]]] = None

class Conclusion(BaseModel):
    status: str = Field(..., description="W‑STATE_CONFIRMED, PARTIAL_W_STATE, NO_W_STATE, DISCRETE_LATTICE_CONFIRMED, FIBONACCI_BRAID_CONFIRMED, PARTIAL_SIGNAL, NO_SIGNAL, INCONCLUSIVE")
    peaks_total: int
    peaks_in_resonance: int
    max_coherence: float
    experimental_gamma5: Optional[float] = None
    interpretation: str
    philosophical_note: str

class AnalysisResponse(BaseModel):
    id: str
    timestamp: str
    data_source: str
    peaks: List[PeakInfo]
    conclusion: Conclusion
    output_file: Optional[str] = None

class TeleportationRequest(BaseModel):
    phases: List[float]
    coherence: List[float]
    nodes: int = Field(3, ge=3)
    loss_probability: float = Field(0.2, ge=0, le=1)

class TeleportationResponse(BaseModel):
    resource_type: str = "W‑State"
    teleportation_ready: bool
    robustness_score: float
    has_2pi3_resonance: bool
    status: str
    interpretation: str
    philosophical_note: str

class OptimizationRequest(BaseModel):
    t_peak: float = Field(30.0, description="Tempo até pico de abertura da BBE (min)")
    t_decay: float = Field(60.0, description="Constante de decaimento da permeabilidade (min)")
    drug_halflife: float = Field(120.0, description="Meia-vida do fármaco na corrente sanguínea (min)")
    microbubbles: bool = True
    mi: float = Field(0.4, description="Mechanical Index (0.1-0.6)")

class OncologyRequest(BaseModel):
    num_cells: int = Field(1000, ge=10, le=10000)
    tumor_fraction: float = Field(0.1, ge=0.01, le=0.5)
    treatment_type: str = "combined" # ivmt, docetaxel, combined, control

class StemCellSafetyRequest(BaseModel):
    ivmt_bandwidth: float = Field(0.05, ge=0.001, le=0.5)
    stem_cell_phase_signature: float = 0.88
    safety_threshold: float = 0.85

class BioSilentRequest(BaseModel):
    base_k: float = 1.0
    distance_to_hospital: float
    exclusion_radius: float = 200.0
    is_manual_override: bool = False
class Lambda2Request(BaseModel):
    signals: List[List[float]] # List of channels, each a list of samples

class EEGSimulationRequest(BaseModel):
    kappa: float = 0.8
    noise_level: float = 0.3
    is_synaesthete: bool = True

class TMSModulationRequest(BaseModel):
    kappa_baseline: float = 0.2
    intensity_percent: float = 65.0
    duration_min: float = 10.0

class AudioColorRequest(BaseModel):
    frequency_hz: float = 440.0
    kappa: float = 0.8

class MaxTokiNVRequest(BaseModel):
    nv_data: List[float] = Field(..., min_length=168, max_length=168)

class MaxTokiTrajectoryRequest(BaseModel):
    current_lambda: float
    tissue_type: str = "cochlea"
    biological_age: float = 0.0
    interventions: Optional[List[str]] = None

class MaxTokiOTOFRequest(BaseModel):
    pre_surgery_lambda: float
    surgical_intervention: str = "AAV_OTOF_Dual"

# --- Endpoints ---

@app.post("/simulate/su2", response_model=CoherenceResponse, tags=["simulation"])
async def simulate_su2(req: SU2Request):
    theta = np.linspace(req.theta_range[0], req.theta_range[1], req.num_points)
    phases, coherence = simulate_su2_continuous(theta, req.thermal_noise, req.temperature)
    return {"phases": phases.tolist(), "coherence": coherence.tolist()}

@app.post("/simulate/sl3z", response_model=CoherenceResponse, tags=["simulation"])
async def simulate_sl3z(req: SL3ZRequest):
    theta = np.linspace(req.theta_range[0], req.theta_range[1], req.num_points)
    phases, coherence = simulate_sl3z_discrete(theta, req.words)
    return {"phases": phases.tolist(), "coherence": coherence.tolist()}

@app.post("/simulate/wstate", response_model=CoherenceResponse, tags=["simulation"])
async def simulate_wstate(req: WStateRequest):
    theta = np.linspace(req.theta_range[0], req.theta_range[1], req.num_points)
    phases, coherence = simulate_w_state_coherence(
        nodes=req.nodes,
        loss_probability=req.loss_probability,
        theta_range=theta
    )
    return {"phases": phases.tolist(), "coherence": coherence.tolist()}

@app.post("/simulate/fibonacci-braid", response_model=FibonacciResponse, tags=["simulation"])
async def simulate_fibonacci(req: FibonacciRequest):
    """
    Real-time assessment of Fibonacci braid realization feasibility.
    """
    result = simulate_fibonacci_braid(
        dalpha=req.dalpha,
        epsilon=req.epsilon,
        eta=req.eta,
        lambda_=req.lambda_param
    )
    return result

@app.post("/simulate/rainbow-coherence", response_model=RainbowResponse, tags=["simulation"])
async def simulate_rainbow(req: RainbowRequest):
    """
    Simulate Rainbow metric deformation based on probe energy.
    """
    params = RainbowParams(
        energy_thz=req.energy_thz,
        num_points=req.num_points,
        resonance_scale=req.resonance_scale
    )
    result = simulate_rainbow_coherence(params)
    return result

@app.post("/synchro/collective_coherence", response_model=CollectiveCoherenceResponse, tags=["synchronization"])
async def collective_coherence_endpoint(req: CollectiveCoherenceRequest):
    """
    Simulate Kuramoto synchronization for collective coherence (v4.0.0).
    """
    params = KuramotoParams(
        nodes=[{"phase": n.phase, "natural_freq": n.natural_freq, "weight": n.weight} for n in req.nodes],
        coupling_K=req.coupling_K,
        time_horizon=req.time_horizon,
        dt=req.dt,
        fusion_threshold=req.fusion_threshold,
        stabilization_time=req.stabilization_time,
        enable_rainbow_resonance=req.enable_rainbow_resonance
    )
    result = simulate_collective_coherence(params)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/synchro/collective_coherence/optimize", tags=["synchronization"])
async def collective_coherence_optimize_endpoint(req: CollectiveCoherenceRequest):
    """
    Finds optimal coupling constant K for fastest fusion.
    """
    params = KuramotoParams(
        nodes=[{"phase": n.phase, "natural_freq": n.natural_freq, "weight": n.weight} for n in req.nodes],
        time_horizon=req.time_horizon,
        dt=req.dt,
        fusion_threshold=req.fusion_threshold,
        stabilization_time=req.stabilization_time,
        enable_rainbow_resonance=req.enable_rainbow_resonance
    )
    result = optimize_coupling(params)
    return result

@app.post("/simulate/xenoactualization", response_model=XenoactualizationResponse, tags=["xenoactualization"])
async def xenoactualization_endpoint(req: XenoactualizationRequest):
    """
    Simulate xenoactualization fidelity with Zeno dynamics.
    """
    params = XenoParams(
        coherence_profile=req.coherence_profile,
        blueprint_complexity=req.blueprint_complexity,
        measurement_rate=req.measurement_rate,
        tau_field_strength=req.tau_field_strength
    )
    result = simulate_xenoactualization(params)
    return result

@app.post("/simulate/xenoactualization/scan", tags=["xenoactualization"])
async def xenoactualization_scan_endpoint(req: XenoactualizationRequest):
    """
    Scans measurement rate to find optimal for maximum fidelity.
    """
    result = scan_optimal_measurement_rate(
        coherence_profile=req.coherence_profile,
        blueprint_complexity=req.blueprint_complexity,
        tau_strength=req.tau_field_strength
    )
    return result

@app.post("/detect/peaks", response_model=PeakDetectionResponse, tags=["detection"])
async def detect_peaks_endpoint(req: PeakDetectionRequest):
    peaks = detect_peaks(
        np.array(req.coherence),
        np.array(req.phases),
        req.threshold_multiplier,
        req.min_prominence,
        req.energy_ev
    )
    return {"peaks": peaks}

@app.post("/detect/rainbow-peaks", response_model=RainbowPeakResponse, tags=["detection"])
async def detect_rainbow_peaks_endpoint(req: PeakDetectionRequest):
    """
    Identifies peaks in coherence data and classifies them according to
    their shift from the base Cartan resonances (π/5, 2π/3).
    """
    result = detect_rainbow_peaks(
        phases=req.phases,
        coherence=req.coherence,
        threshold=req.threshold or 0.3
    )
    return result

@app.post("/analyze", response_model=AnalysisResponse, tags=["analysis"])
async def analyze_endpoint(req: AnalysisRequest):
    """
    Complete interrogation pipeline.
    """
    timestamp = datetime.now().isoformat()
    analysis_id = str(uuid.uuid4())

    if req.data_source == "experimental":
        if not req.experimental_data or "phases" not in req.experimental_data or "coherence" not in req.experimental_data:
            raise HTTPException(status_code=400, detail="Experimental data missing")
        phases = np.array(req.experimental_data["phases"])
        coherence = np.array(req.experimental_data["coherence"])
    else:
        # Generate simulated data (Hybrid by default if not specified)
        theta = np.linspace(0.01, 2 * np.pi, 1000)

        # SU(2) component
        su2_p = req.su2_params or SU2Request(num_points=1000)
        _, coh_su2 = simulate_su2_continuous(theta, su2_p.thermal_noise, su2_p.temperature)

        # SL(3,Z) component
        sl3z_p = req.sl3z_params or SL3ZRequest(num_points=1000)
        _, coh_sl3 = simulate_sl3z_discrete(theta, sl3z_p.words)

        phases = theta
        coherence = 0.3 * coh_su2 + 0.7 * coh_sl3

    # Detection
    det_p = req.detection_params or {"threshold_multiplier": 1.2, "min_prominence": 0.05}
    peaks = detect_peaks(
        coherence,
        phases,
        det_p.get("threshold_multiplier", 1.2),
        det_p.get("min_prominence", 0.05)
    )

    # Conclusion
    conclusion = synthesize_conclusion(peaks, threshold=0.95)

    return {
        "id": analysis_id,
        "timestamp": timestamp,
        "data_source": req.data_source,
        "peaks": peaks,
        "conclusion": conclusion
    }

@app.post("/analyze/teleportation-resource", response_model=TeleportationResponse, tags=["teleportation"])
async def check_w_state(req: TeleportationRequest):
    """
    Assess whether the measured coherence matches a W‑state profile.
    Returns a teleportation readiness score and a verdict.
    """
    # Generate ideal W‑state profile
    theta_range, w_profile = simulate_w_state_coherence(
        nodes=req.nodes,
        loss_probability=req.loss_probability,
        theta_range=np.array(req.phases)
    )

    # Detect peaks in measured data
    # Use standard defaults
    measured_peaks = detect_peaks(np.array(req.coherence), np.array(req.phases))

    # Check for 2π/3 resonance (tripartite peak)
    target = 2 * np.pi / 3
    tolerance = 0.15
    has_resonance = any(abs(p['phase'] - target) < tolerance for p in measured_peaks)

    # Compute robustness score (normalized cross‑correlation between measured and ideal)
    norm_measured = np.array(req.coherence) / (np.linalg.norm(req.coherence) + 1e-15)
    norm_profile = w_profile / (np.linalg.norm(w_profile) + 1e-15)
    robustness = float(np.clip(np.sum(norm_measured * norm_profile), 0, 1))

    # Synthesise conclusion
    if has_resonance and robustness > 0.7:
        status = "W‑STATE_CONFIRMED"
        interpretation = "Strong W‑state signature detected. Teleportation resource available."
        teleportation_ready = True
    elif robustness > 0.5:
        status = "PARTIAL_W_STATE"
        interpretation = "Partial W‑state coherence; possible mixed state or incomplete entanglement."
        teleportation_ready = False
    else:
        status = "NO_W_STATE"
        interpretation = "No W‑state coherence detected. Teleportation not feasible."
        teleportation_ready = False

    # Get philosophical note from existing synthesis logic
    conclusion = synthesize_conclusion(measured_peaks, threshold=0.95)

    return {
        "resource_type": "W‑State",
        "teleportation_ready": teleportation_ready,
        "robustness_score": robustness,
        "has_2pi3_resonance": has_resonance,
        "status": status,
        "interpretation": interpretation,
        "philosophical_note": conclusion["philosophical_note"]
    }

@app.post("/validate/lambda2", tags=["synapse-k"])
async def validate_lambda2(req: Lambda2Request):
    """Calcula a coerência λ₂ para sinais multi-canal."""
    l2 = lambda2_coherence(np.array(req.signals))
    return {"lambda2": l2}

@app.post("/simulate/synapse-k/eeg", tags=["synapse-k"])
async def simulate_synapse_k_eeg(req: EEGSimulationRequest):
    """Simula sinais EEG para sinestetas ou controles e valida."""
    validator = SynapseKValidator()
    if req.is_synaesthete:
        data = validator.generate_eeg_synapse(req.kappa, req.noise_level)
    else:
        data = validator.generate_eeg_control(req.noise_level)

    validation = validator.validate_synaesthete(data)
    # Convert numpy arrays to lists for JSON serialization
    serialized_data = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in data.items()}
    return {"eeg_data": serialized_data, "validation": validation}

@app.post("/simulate/synapse-k/tms", tags=["synapse-k"])
async def simulate_synapse_k_tms(req: TMSModulationRequest):
    """Modela a modulação do coeficiente κ via TMS."""
    tms = TMSModulator()
    k_new = tms.modulate_kappa(req.kappa_baseline, req.intensity_percent, req.duration_min)
    return {"kappa_new": k_new}

@app.post("/map/audio-to-color", tags=["synapse-k"])
async def map_audio_to_color(req: AudioColorRequest):
    """Mapeia uma frequência auditiva para o espaço cromático Synapse-κ."""
    interface = ARChromestheticInterface()
    color = interface.audio_to_color(req.frequency_hz, req.kappa)
    return color

@app.post("/therapy/optimize-combined-protocol", tags=["therapy"])
async def optimize_combined_protocol(req: OptimizationRequest):
    """
    Retorna o intervalo ideal entre LIPUS e administração de fármaco,
    bem como a absorção esperada.
    """
    result = optimize_lipus_drug_interval(
        t_peak=req.t_peak,
        t_decay=req.t_decay,
        drug_halflife=req.drug_halflife,
        microbubbles=req.microbubbles,
        mi=req.mi
    )
    # Adiciona nota filosófica
    result["philosophical_note"] = (
        "A janela de oportunidade é o intervalo onde a permeabilidade da barreira "
        "e a presença do fármaco se entrelaçam. O ultrassom abre a cancela; o relógio "
        "do medicamento decide se a cura chegará a tempo."
    )
    return result

@app.post("/therapy/phase-oncology", tags=["therapy"])
async def phase_oncology_endpoint(req: OncologyRequest):
    """
    Simula a Terapia de Fase (Phase Therapy) em uma rede celular tumorígena.
    Modela o colapso de coerência seletivo via IVMT-Rx-4 e Docetaxel.
    """
    result = simulate_phase_oncology(
        num_cells=req.num_cells,
        tumor_fraction=req.tumor_fraction,
        treatment_type=req.treatment_type
    )
    return result

@app.post("/therapy/stem-cell-safety", tags=["therapy"])
async def stem_cell_safety_endpoint(req: StemCellSafetyRequest):
    """
    Avalia a segurança de fase para Células-Tronco Hematopoiéticas (CTHs)
    sob a influência da janela de decoerência do IVMT-Rx-4.
    """
    result = simulate_stem_cell_safety(
        ivmt_bandwidth=req.ivmt_bandwidth,
        stem_cell_phase_signature=req.stem_cell_phase_signature,
        safety_threshold=req.safety_threshold
    )
    return result

@app.post("/therapy/bio-silent", tags=["therapy"])
async def bio_silent_endpoint(req: BioSilentRequest):
    """
    Calcula o acoplamento reduzido para zonas hospitalares sensíveis.
    """
    k_eff = calculate_bio_silent_coupling(
        base_k=req.base_k,
        distance_to_hospital=req.distance_to_hospital,
        exclusion_radius=req.exclusion_radius,
        is_manual_override=req.is_manual_override
    )
    return {"effective_k": round(float(k_eff), 4), "status": "BIO_SILENT_ACTIVE" if k_eff == 0 else "NORMAL"}

@app.post("/therapy/optimize-combined-protocol-legacy", tags=["therapy"], include_in_schema=False)
async def optimize_combined_protocol_legacy(req: OptimizationRequest):
    """
    Retorna o intervalo ideal entre LIPUS e administração de fármaco,
    bem como a absorção esperada.
    """
    result = optimize_lipus_drug_interval(
        t_peak=req.t_peak,
        t_decay=req.t_decay,
        drug_halflife=req.drug_halflife,
        microbubbles=req.microbubbles,
        mi=req.mi
    )
    # Adiciona nota filosófica
    result["philosophical_note"] = (
        "A janela de oportunidade é o intervalo onde a permeabilidade da barreira "
        "e a presença do fármaco se entrelaçam. O ultrassom abre a cancela; o relógio "
        "do medicamento decide se a cura chegará a tempo."
    )
    return result
# --- MaxToki Endpoints ---

@app.post("/maxtoki/screen-eligibility", tags=["maxtoki"])
async def maxtoki_screen_eligibility(req: MaxTokiNVRequest):
    """
    Triagem de elegibilidade para terapia usando MaxToki.
    Verifica se o perfil celular é compatível com sucesso terapêutico.
    """
    integration = ArkheMaxTokiIntegration()
    nv_data = np.array(req.nv_data)
    result = integration.screen_patient_eligibility(nv_data)
    return result

@app.post("/maxtoki/predict-trajectory", tags=["maxtoki"])
async def maxtoki_predict_trajectory(req: MaxTokiTrajectoryRequest):
    """
    Prediz a trajetória de envelhecimento/rejuvenescimento celular.
    """
    integration = ArkheMaxTokiIntegration()
    current_state = CellularState(
        timestamp=datetime.now(),
        lambda_coherence=req.current_lambda,
        transcriptome_vector=np.zeros(20271), # Placeholder
        biological_age=req.biological_age,
        tissue_type=req.tissue_type
    )
    trajectory = integration.maxtoki.predict_aging_trajectory(
        current_state=current_state,
        interventions=req.interventions
    )

    return trajectory.to_dict()

@app.post("/maxtoki/predict-otof-recovery", tags=["maxtoki"])
async def maxtoki_predict_otof_recovery(req: MaxTokiOTOFRequest):
    """
    Prediz a curva de recuperação auditiva (dB) específica para terapia OTOF.
    """
    integration = ArkheMaxTokiIntegration()
    pre_state = CellularState(
        timestamp=datetime.now(),
        lambda_coherence=req.pre_surgery_lambda,
        transcriptome_vector=np.zeros(20271), # Placeholder
        biological_age=0.0,
        tissue_type="cochlea"
    )
    prediction = integration.maxtoki.predict_otof_recovery(
        pre_surgery_state=pre_state,
        surgical_intervention=req.surgical_intervention
    )

    # Remove transcript vectors from response for size
    del prediction['trajectory']

    return prediction

@app.post("/maxtoki/generate-contract", tags=["maxtoki"])
async def maxtoki_generate_contract(req: MaxTokiNVRequest):
    """
    Gera dados formatados para smart contracts $RIO com milestones baseados no MaxToki.
    """
    integration = ArkheMaxTokiIntegration()
    nv_data = np.array(req.nv_data)
    screening = integration.screen_patient_eligibility(nv_data)
    return integration.generate_smart_contract_data(screening)

@app.websocket("/therapy/monitoring")
async def websocket_glymphatic_monitor(websocket: WebSocket):
    await websocket.accept()
    try:
        # Parâmetros da sessão (enviados uma vez na primeira mensagem)
        session_params = await websocket.receive_json()
        lipus_intensity = session_params.get("lipus_intensity_mw_cm2", 150.0)
        baseline_coherence = session_params.get("baseline_coherence", 0.3)

        # Parâmetros Fibonacci (opcionais) para avaliação de trança em tempo real
        fib_params = session_params.get("fibonacci_params", {})

        while True:
            # Recebe pacote com dados de coerência em tempo real
            data = await websocket.receive_json()
            fret_coherence = data.get("fret_coherence")
            phase_angle = data.get("phase_angle", 0.0)
            elapsed_minutes = data.get("elapsed_minutes", 0.0)

            if fret_coherence is None:
                await websocket.send_json({"error": "Missing fret_coherence"})
                continue

            # Estimativa de Limpeza
            result = estimate_glymphatic_clearance(
                fret_coherence=fret_coherence,
                phase_angle=phase_angle,
                lipus_intensity_mw_cm2=lipus_intensity,
                elapsed_minutes=elapsed_minutes,
                baseline_coherence=baseline_coherence
            )

            # Se parâmetros de Fibonacci foram fornecidos, realiza avaliação de trança
            if fib_params:
                braid_eval = simulate_fibonacci_braid(
                    dalpha=fib_params.get("dalpha", 0.0),
                    epsilon=fib_params.get("epsilon", 0.0),
                    eta=fib_params.get("eta", 0.0),
                    lambda_=fib_params.get("lambda", 0.0)
                )
                result["fibonacci_braid_assessment"] = braid_eval

            await websocket.send_json(result)

    except WebSocketDisconnect:
        logger.info("Cliente desconectado do monitoramento")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
