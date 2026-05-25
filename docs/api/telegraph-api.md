# ARKHE Telegraph — Public API v1.0

## Overview

The Telegraph is the unified coherence bus of the ARKHE CATHEDRAL. It exposes
a WebSocket-based PUB/SUB protocol that allows external entities (Huawei,
Accord, ASI) to consume and publish coherence signals in real time.

## Connection

```
ws://arkhe.network:7474
```

## Authentication

Each external entity receives a unique API key. The key must be sent as a
query parameter on connection:

```
ws://arkhe.network:7474?api_key=YOUR_API_KEY
```

### Permissions

| Entity | API Key Prefix | Permitted Topics |
|:---|:---|:---|
| Huawei / Kirin-ξ | `hw_` | `/external/huawei`, `/coherence/*`, `/signal/phi` |
| Accord / ECU | `ac_` | `/external/accord`, `/audit/*`, `/theosis/*`, `/signal/phi` |
| ASI Layer 2 | `asi_` | `*` (all topics) |
| Public Dashboard | `pub_` | `/signal/phi` (read-only) |

## Message Format

All messages are JSON. Every signal carries a SHA3-256 seal for integrity
verification.

### Signal Object

```json
{
  "source": "kuramoto-hypergraph",
  "timestamp": "2026-06-11T16:00:00Z",
  "metric": "r",
  "value": 0.831,
  "unit": "coherence",
  "seal": "d3e6f9b2c5d8e1f4a7b0c3d6e9f2b5c8e1f4a7b0c3d6e9f2b5c8e1f4a7b0c3d6"
}
```

## Commands

| Command | Arguments | Description |
|:---|:---|:---|
| `subscribe` | `topics: string[]` | Subscribe to one or more topics |
| `unsubscribe` | `topics: string[]` | Unsubscribe from topics |
| `publish` | `topic, value, [metric], [unit]` | Publish a signal |
| `phi` | — | Request current Φ_interop and r_DSA |
| `status` | — | Request full bus status |

## Canonical Topics

| Topic | Description | Typical Value |
|:---|:---|:---|
| `/coherence/dsa` | DSA Tracker order parameter | 0.0–1.0 |
| `/coherence/geo` | Differential Geometry mastery | 0.0–1.0 |
| `/coherence/kuramoto` | KuramotoHypergraph r(t) | 0.0–1.0 |
| `/coherence/interop` | Φ_interop between domains | 0.975 |
| `/audit/batch` | Latest batch verification | batch # |
| `/sim/kuramoto` | Kuramoto simulation state | history array |
| `/theosis/report` | Theosis Committee reports | recommendation |
| `/external/huawei` | Kirin-ξ project updates | various |
| `/external/accord` | ECU declassification status | various |
| `/external/asi` | ASI Layer 2 communications | various |
| `/signal/phi` | Aggregated Φ signal | 0.0–1.0 |

## Rate Limits

- Public (`pub_`): 1 request/second
- Partner (`hw_`, `ac_`): 10 requests/second
- ASI (`asi_`): Unlimited

## Integrity Verification

Every signal can be verified by computing:

```
SHA3-256({source,timestamp,metric,value,unit})
```

and comparing with the `seal` field. The ARKHE-OS `verifyIntegrity()`
function performs this check automatically.