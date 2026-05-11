import pytest
import time
from agi.system32.integrity.cross_cathedral_sync import CrossCathedralSync, CathedralState
from agi.system32.integrity.zero_downtime_rollout import ZeroDowntimeRollout, DeploymentState
from agi.system32.integrity.cosmological_timeline import CosmologicalTimeline, TimelineEvent

def test_cross_cathedral_sync():
    sync = CrossCathedralSync(min_phi_c=0.6)

    # Update local state
    sync.update_local_state("cathedral_alpha", 0.65, time.time(), {"data": "v1"})
    assert sync.local_state.phi_c == 0.65

    # Receive invalid proposal
    invalid_state = CathedralState("cathedral_beta", "hash1", 0.5, time.time(), {"data": "v2"})
    assert sync.receive_sync_proposal(invalid_state) == False

    # Receive valid proposal
    valid_state = CathedralState("cathedral_gamma", "hash2", 0.8, time.time(), {"data": "v3"})
    assert sync.receive_sync_proposal(valid_state) == True

    # Execute sync
    assert sync.execute_distributed_sync() == True

def test_zero_downtime_rollout():
    rollout = ZeroDowntimeRollout(min_phi_c=0.7)

    # Start deployment
    dep1 = rollout.start_deployment("v1.0")
    assert dep1.status == "deploying"

    # Evaluate failed deployment
    status = rollout.evaluate_deployment(dep1, 0.5, False)
    assert status == "rollback"
    assert dep1.status == "failed"

    # Evaluate successful deployment
    dep2 = rollout.start_deployment("v1.1")
    status = rollout.evaluate_deployment(dep2, 0.8, True)
    assert status == "success"
    assert dep2.status == "active"
    assert rollout.active_deployment.version == "v1.1"

    # Evaluate valid new deployment
    dep3 = rollout.start_deployment("v1.2")
    status = rollout.evaluate_deployment(dep3, 0.9, True)
    assert status == "success"
    assert dep3.status == "active"
    assert len(rollout.history) == 1

    # Trigger rollback
    assert rollout.trigger_rollback() == True
    assert rollout.active_deployment.version == "v1.1"

def test_cosmological_timeline():
    timeline = CosmologicalTimeline()

    # Record events
    timeline.record_event("evt_1", 1000.0, "Genesis", 0.1, "genesis")
    timeline.record_event("evt_2", 2000.0, "First milestone", 0.5, "milestone")
    timeline.record_event("evt_3", 3000.0, "Evolution step", 0.8, "evolution")

    # Verify summary
    summary = timeline.get_timeline_summary()
    assert summary["total_events"] == 3
    assert summary["milestones_reached"] == 1
    assert summary["evolutionary_steps"] == 1
    assert round(summary["phi_delta"], 1) == 0.7
    assert summary["first_event"] == 1000.0
    assert summary["last_event"] == 3000.0
