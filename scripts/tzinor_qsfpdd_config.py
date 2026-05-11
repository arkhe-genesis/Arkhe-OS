#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tzinor_qsfpdd_config.py
Generates configuration files for 14 QSFP-DD 400G nodes in the Tzinor network.
Includes latency targets, pre-ACK windows, and DWDM channel allocation.
"""

import json
import os

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================
N_NODES = 14
CHANNELS = [f"C{21+i}" for i in range(N_NODES)]
NODES = [
    "Central", "Carioca", "Uruguaiana", "Presidente Vargas", "Porto",
    "tunnel_01", "tunnel_02", "tunnel_03", "tunnel_04", "tunnel_05",
    "tunnel_06", "tunnel_07", "tunnel_08", "tunnel_09"
]

def generate_configs():
    print(f"📦 Generating QSFP-DD configurations for {N_NODES} nodes...")

    master_config = {
        "network": "Tzinor-Rio",
        "protocol": "qhttp/retro-arq",
        "total_nodes": N_NODES,
        "nodes": []
    }

    for i, name in enumerate(NODES):
        node_id = f"TZ-{name}"
        config = {
            "node_id": node_id,
            "transceiver": "QSFP-DD-400G-ZR",
            "dwdm_channel": CHANNELS[i],
            "modulation": "PAM4_BIO_PHASE",
            "signature_algorithm": "ml-dsa-65",
            "latency_target_ns": 15.0,
            "pre_ack_window_ns": 15.0,
            "coherence_target": 0.985,
            "safety_thresholds": {
                "vibration_g": 0.05,
                "temperature_c": 42.0
            }
        }

        # Individual JSON
        config_file = f"tzinor_node_{name}_config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        # Individual Setup Shell Script
        setup_file = f"tzinor_node_{name}_setup.sh"
        with open(setup_file, "w") as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"# Setup script for {node_id}\n")
            f.write(f"echo \"Configuring {node_id} on channel {CHANNELS[i]}...\"\n")
            f.write(f"load_config \"{config_file}\"\n")
            f.write(f"set_modulation PAM4_BIO_PHASE\n")
            f.write(f"echo \"Node {node_id} READY.\"\n")

        master_config["nodes"].append(config)

    with open("tzinor_network_config.json", "w") as f:
        json.dump(master_config, f, indent=2)

    print(f"✅ Master configuration and {N_NODES} node files generated.")

if __name__ == "__main__":
    generate_configs()
