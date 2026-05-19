import pytest
import json
import asyncio
import sys
from unittest.mock import MagicMock

# Mock Arkhe modules before importing CloudIntegration
sys.modules['arkhe_crypto'] = MagicMock()
sys.modules['arkhe_bus'] = MagicMock()
sys.modules['arkhe_temporal'] = MagicMock()

class MockTemporalChain:
    async def anchor_event(self, event, data):
        pass

class MockArkheKMS:
    def generate_data_key(self):
        return b"mock"
    def encrypt(self, data):
        return b"mock-encrypted"

sys.modules['arkhe_temporal'].TemporalChain = MockTemporalChain
sys.modules['arkhe_crypto'].ArkheKMS = MockArkheKMS

from arkhe.cloud.integration import CloudIntegration
import botocore.session
from botocore.stub import Stubber

@pytest.fixture
def integration():
    return CloudIntegration(region="us-east-1")

@pytest.fixture
def bedrock_stubber(integration):
    stubber = Stubber(integration.bedrock)
    stubber.activate()
    yield stubber
    stubber.deactivate()

@pytest.fixture
def sagemaker_stubber(integration):
    stubber = Stubber(integration.sagemaker)
    stubber.activate()
    yield stubber
    stubber.deactivate()


@pytest.mark.asyncio
async def test_sagemaker_start_training_job(integration, sagemaker_stubber):
    job_name = "arkhe-model-v1"
    config = {
        "training_image": "mock-image",
        "role_arn": "arn:aws:iam::123456789012:role/Arkhe-Training-Role-P7",
        "s3_uri": "s3://mock-bucket/input/",
        "output_s3_uri": "s3://mock-bucket/output/",
        "instance_type": "ml.p3.2xlarge",
        "hyperparameters": {"epochs": "3"}, "kms_key_arn": "arn:aws:kms:mock"
    }

    expected_response = {
        "TrainingJobArn": "arn:aws:sagemaker:us-east-1:123456789012:training-job/arkhe-model-v1-1234567890"
    }

    # Ignore exact time values for the test
    sagemaker_stubber.add_response(
        "create_training_job",
        expected_response,
        # Any request parameters are accepted
    )

    result = await integration.start_training_job(job_name, config)
    assert result["job_arn"] == expected_response["TrainingJobArn"]
    assert result["status"] == "started"


@pytest.mark.asyncio
async def test_bedrock_invoke_model(integration, bedrock_stubber):
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    prompt = "Test prompt"

    import io
    # Mock response body
    response_body = json.dumps({
        "content": [{"text": "P1-P7 principles respected. Arkhe is canonical."}]
    }).encode("utf-8")

    # Needs to simulate StreamingBody
    from botocore.response import StreamingBody
    streaming_body = StreamingBody(io.BytesIO(response_body), len(response_body))

    expected_response = {
        "body": streaming_body,
        "contentType": "application/json"
    }

    bedrock_stubber.add_response(
        "invoke_model",
        expected_response,
        # Accept any valid request params
    )

    result = await integration.invoke_bedrock_model(model_id, prompt)
    assert "response" in result
    assert "phi_c_score" in result
    assert result["phi_c_score"] > 0
    assert result["model_id"] == model_id
