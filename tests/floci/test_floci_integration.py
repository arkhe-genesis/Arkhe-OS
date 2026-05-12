import pytest
import boto3
import requests
import time

@pytest.fixture(scope="session")
def s3_client():
    # Retry logic to wait for floci container to start if it's running via docker-compose
    endpoint = "http://localhost:4566"
    max_retries = 30
    for _ in range(max_retries):
        try:
            r = requests.get(f"{endpoint}/_localstack/health", timeout=2) # floci serves this endpoint for compatibility
            if r.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(1)
            continue
    else:
        pytest.skip("Floci is not running on localhost:4566, skipping integration test.")

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    return client

def test_floci_s3_bucket(s3_client):
    bucket_name = "test-floci-bucket"
    s3_client.create_bucket(Bucket=bucket_name)
    response = s3_client.list_buckets()
    buckets = [b["Name"] for b in response.get("Buckets", [])]
    assert bucket_name in buckets

    # Cleanup
    s3_client.delete_bucket(Bucket=bucket_name)
