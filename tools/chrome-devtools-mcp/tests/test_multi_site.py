from core.protocol.multi_site_sync import OrthogonalWitnessSummary, MultiSiteTrialCoordinator

def test_multi_site():
    summary = OrthogonalWitnessSummary(
        cohort_id="c1",
        aggregated_pdi_trajectory=[0.5, 0.6],
        average_k_target=0.07,
        mercy_gap_compliance_rate=0.9,
        zk_proof_of_aggregation=b"zk_proof_valid"
    )
    coord = MultiSiteTrialCoordinator("t1")
    assert coord.submit_site_summary("s1", summary) == True
    state = coord.get_global_trial_state()
    assert state["global_pdi_consensus"] == 0.6
