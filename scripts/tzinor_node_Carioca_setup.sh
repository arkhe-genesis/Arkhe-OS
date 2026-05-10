#!/bin/bash
# Setup script for TZ-Carioca
echo "Configuring TZ-Carioca on channel C22..."
load_config "tzinor_node_Carioca_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-Carioca READY."
