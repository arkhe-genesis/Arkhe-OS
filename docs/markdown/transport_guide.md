# TransportAdapter Guide

## Overview

The `TransportAdapter` (Substrate 326.1) provides a unified interface for coherence-aware routing across multiple transport protocols (Tor, DnsVPN, Stream, Direct TCP). It dynamically selects the transport protocol based on a historical Coherence Transport Score (CTS), tracking metrics such as latency, packet loss rate, jitter, and connection status.

## Configuration

The main configuration file is located at `config/yaml/transport.yaml`. You can modify the priorities and CTS weights directly.

## Usage

Use the CLI interface via the command wrapper:

```bash
agictl transport status
agictl transport test check.torproject.org:80
```

## Troubleshooting

- `ModuleNotFoundError`: Ensure your `PYTHONPATH` includes the repository root.
- `Tor Control Port Connection Failed`: Verify Tor is running locally.
# Transport Guide
## Configuration and Troubleshooting

This guide provides instructions on how to configure and troubleshoot the TransportAdapter (Substrate 326.1).

* To check the status of the transports: `agictl transport status`
* To test the transport: `agictl transport test <destination>`
