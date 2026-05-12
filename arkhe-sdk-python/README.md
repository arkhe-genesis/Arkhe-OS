# Arkhe OS SDK

This is the Python SDK for Arkhe OS Client Enterprise Edition.

## Installation

You can install this via Poetry:
```bash
poetry install
```

## Usage

Check the `examples/example_usage.py` for a detailed example.

```python
import asyncio
from arkhe_sdk.services.client import ArkheClient
from arkhe_sdk.models.coherence import ValidationRequest

async def main():
    async with ArkheClient("http://localhost:8080", "fake_token") as client:
        # Check health
        health = await client.get_health()
        print(f"Health status: {health.status}")

if __name__ == "__main__":
    asyncio.run(main())
```
