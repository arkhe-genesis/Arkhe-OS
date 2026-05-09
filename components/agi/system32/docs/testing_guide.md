# ARKHE OS AGI Core Testing Guide

## Test Suites

The AGI Core comes with an automated testing suite to validate retrocausal coherence and OmniNet integration.

### RCP v2.0 Fidelity Tests

Validates the integrity of the 8-bit retrocausal channel.

```bash
cd agi/system32/test
python3 test_fidelity_suite.py
```

### OmniNet Integration Tests

Validates hybrid quantum-classical networking.

```bash
cd agi/system32/test
python3 test_omninet_integration.py
```

## Requirements

Ensure the Python environment has the necessary testing dependencies:
- `pytest`
- `numpy`
- `scipy`
