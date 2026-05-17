import pytest
import time
import json
import hashlib
from opencode.opencode_advanced import (
    OpenCodeAutoScaler, ScaleDirection, ScalingMetrics,
    PromptRLOptimizer, PromptActionSpace,
    ConfigFederationService, ConfigVisibility, FederatedConfig
)

class MockTemporalChain:
    """Mock for TemporalChain anchoring."""
    async def anchor_event(self, event_type: str, data: dict):
        return f"mock_seal_{event_type}_{hash(str(data))}"

# --- Test OpenCodeAutoScaler ---

def test_autoscaler_collect_metrics():
    scaler = OpenCodeAutoScaler()
    metrics = scaler.collect_metrics()
    assert isinstance(metrics, ScalingMetrics)
    assert 5 <= metrics.active_sessions <= 40
    assert 0 <= metrics.pending_prompts <= 30
    assert 0.85 <= metrics.system_phi_c <= 1.0

def test_autoscaler_evaluate_policy_scale_up():
    scaler = OpenCodeAutoScaler()
    metrics = ScalingMetrics(
        active_sessions=10,
        pending_prompts=25, # High pending prompts > 20
        avg_latency_ms=2500, # High latency > 2000
        system_phi_c=0.95,
        token_usage_rate=0.8,
        worker_health_ratio=0.85 # Low health < 0.90
    )
    decision = scaler.evaluate_scaling_policy(metrics)
    assert decision.direction == ScaleDirection.UP
    assert decision.target_replicas > scaler._current_replicas

def test_autoscaler_evaluate_policy_scale_down():
    scaler = OpenCodeAutoScaler()
    scaler._current_replicas = 20 # Need to be above min_replicas to scale down

    # 2 active / 50 max = 4% utilization (< 20%)
    metrics = ScalingMetrics(
        active_sessions=2,
        pending_prompts=0,
        avg_latency_ms=200,
        system_phi_c=0.75, # Low phi_c < 0.80
        token_usage_rate=0.2, # Low token usage < 0.3
        worker_health_ratio=1.0
    )
    decision = scaler.evaluate_scaling_policy(metrics)
    assert decision.direction == ScaleDirection.DOWN
    assert decision.target_replicas < scaler._current_replicas

def test_autoscaler_evaluate_policy_maintain():
    scaler = OpenCodeAutoScaler()
    # Need to be within cooldown or normal bounds
    metrics = ScalingMetrics(
        active_sessions=15, # 30% utilization
        pending_prompts=5,
        avg_latency_ms=500,
        system_phi_c=0.85,
        token_usage_rate=0.5,
        worker_health_ratio=0.95
    )
    decision = scaler.evaluate_scaling_policy(metrics)
    assert decision.direction == ScaleDirection.MAINTAIN
    assert decision.target_replicas == scaler._current_replicas


# --- Test PromptRLOptimizer ---

def test_prompt_optimizer_optimize():
    optimizer = PromptRLOptimizer()
    original_prompt = "Explain quantum computing"
    context = {"lang": "python"}

    optimized_prompt, meta = optimizer.optimize_prompt(original_prompt, context, max_iterations=3)

    assert isinstance(optimized_prompt, str)
    assert isinstance(meta, dict)
    assert "iterations" in meta
    assert "final_phi_c" in meta
    assert "actions_taken" in meta
    assert len(meta["actions_taken"]) <= 3

def test_prompt_action_space():
    prompt = "Test prompt"
    formal_prompt = PromptActionSpace.apply_action(prompt, "rephrase_formal")
    assert "Please provide a formal" in formal_prompt
    assert prompt in formal_prompt

def test_prompt_optimizer_statistics():
    optimizer = PromptRLOptimizer()
    stats_before = optimizer.get_optimizer_statistics()
    assert stats_before["experiences"] == 0

    optimizer.optimize_prompt("Test", {}, max_iterations=2)
    stats_after = optimizer.get_optimizer_statistics()
    assert "total_experiences" in stats_after
    assert stats_after["total_experiences"] > 0


# --- Test ConfigFederationService ---

@pytest.fixture
def federation_service():
    return ConfigFederationService("org_test")

def test_federation_validate_config(federation_service):
    # Valid config
    valid_config = {
        "arkhe_metadata": {"phi_c_threshold": 0.90},
        "tools": ["read", "write"]
    }
    is_valid, reason = federation_service.validate_config_content(valid_config)
    assert is_valid is True

    # Invalid config (missing arkhe_metadata)
    invalid_config1 = {"tools": ["read", "write"]}
    is_valid, reason = federation_service.validate_config_content(invalid_config1)
    assert is_valid is False
    assert "Missing required arkhe_metadata" in reason

    # Invalid config (phi_c_threshold too low)
    invalid_config2 = {
        "arkhe_metadata": {"phi_c_threshold": 0.70}
    }
    is_valid, reason = federation_service.validate_config_content(invalid_config2)
    assert is_valid is False
    assert "phi_c_threshold too low" in reason

def test_federation_create_and_request(federation_service):
    config_content = {
        "arkhe_metadata": {"phi_c_threshold": 0.88},
        "assistant": {"model": "test_model"}
    }

    # Create federated config
    config = federation_service.create_federated_config(
        config_content,
        ConfigVisibility.FEDERATED,
        {"org_allowed"}
    )

    assert isinstance(config, FederatedConfig)
    assert config.config_id in federation_service._local_configs

    # Test request access (allowed org)
    requested_config = federation_service.request_config(config.config_id, "org_allowed")
    assert requested_config is not None
    assert requested_config.config_id == config.config_id

    # Test request access (denied org)
    requested_config_denied = federation_service.request_config(config.config_id, "org_denied")
    assert requested_config_denied is None

def test_federation_receive_config(federation_service):
    # Mock a received config with correct signature
    config_id = "test_config_id"
    org_id = "org_remote"
    pqc_sig = hashlib.sha3_256(f"{config_id}:{org_id}".encode()).hexdigest()

    config_data = {
        "config_id": config_id,
        "config_content": {"arkhe_metadata": {"phi_c_threshold": 0.90}},
        "created_by": "remote_user",
        "organization_id": org_id,
        "visibility": ConfigVisibility.PUBLIC.value,
        "phi_c_score": 0.90,
        "allowed_organizations": [],
        "version": 1,
        "parent_config_id": None,
        "pqc_signature": pqc_sig,
        "temporal_seal": "seal_123",
        "created_at": time.time(),
        "updated_at": None
    }

    result = federation_service.receive_federated_config(config_data)
    assert result is True
    assert config_id in federation_service._received_configs

    # Verify signature fails
    config_data["pqc_signature"] = "invalid_sig"
    result_invalid = federation_service.receive_federated_config(config_data)
    assert result_invalid is False
