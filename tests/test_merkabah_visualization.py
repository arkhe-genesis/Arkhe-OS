from core.merkabah.merkaba_state_vector import MerkabaStateVector, EEGFace, fNIRSFace, HRVFace, BehavioralFace, CrossModalFirmament, MercyGapFlame, Direction, WheelState
from core.visualization.trajectory.sovereign_visualization import SovereignTimeline, RenderConfiguration, DissolutionMandalaRenderer, DecryptedTrajectory
from core.regulatory.regulatory_automation import RegulatoryComplianceCompiler, EthicalLedger, InspectorAuditDashboard

def test_merkaba_state_vector():
    msv = MerkabaStateVector(
        face_human=EEGFace(theta=0.1),
        face_lion=fNIRSFace(hbo_ratio=1.0),
        face_ox=HRVFace(hrv_phase=0.5),
        face_eagle=BehavioralFace(event_count=5),
        firmament=CrossModalFirmament(plv=0.9),
        coals=MercyGapFlame(intensity=0.07),
        wheels=[WheelState(wheel_id="w1", rim=0.8, hub=0.07, spokes=4, rotation=2.0, intersection=None)],
        kavod=0.8,
        voice=b"sig"
    )
    movement = msv.move(Direction(forward=0.1, right=0.2, left=0.1, upward=2.0))
    assert movement.forward == 0.2
    assert movement.upward == 7

def test_sovereign_visualization():
    config = RenderConfiguration()
    renderer = DissolutionMandalaRenderer((1920, 1080))
    trajectory = DecryptedTrajectory()

    frame = renderer.render_frame(trajectory, 1000.0, config)
    assert frame.shape == (1080, 1920, 4)

def test_regulatory_automation():
    compiler = RegulatoryComplianceCompiler("did:trial:1", "did:inspector:1")
    report = compiler.compile_safety_report((0, 1000))
    assert len(report.events) == 1
    assert report.aggregate_metrics.total_events == 1
