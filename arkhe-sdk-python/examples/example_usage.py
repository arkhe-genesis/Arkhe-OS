import asyncio
from arkhe_sdk.services.client import ArkheClient
from arkhe_sdk.models.coherence import ValidationRequest

async def main():
    async with ArkheClient("http://localhost:8080", "fake_token") as client:
        # Check health
        health = await client.get_health()
        print(f"Health status: {health.status}")

        # Submit validation
        request = ValidationRequest(
            experiment_type="quantum_simulation",
            material="herbertsmithite",
            data_hash="abc123hash",
            cves=["CVE-2023-1234"],
            meta={"notes": "initial test"}
        )
        response = await client.submit_validation(request)
        print(f"Validation submitted: {response}")

        # Listen to stream
        # async for msg in client.stream_coherence():
        #     print(f"Coherence update: {msg}")

if __name__ == "__main__":
    asyncio.run(main())
