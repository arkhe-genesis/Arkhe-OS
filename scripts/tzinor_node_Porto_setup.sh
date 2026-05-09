#!/bin/bash
# Setup script for TZ-Porto
echo "Configuring TZ-Porto on channel C25..."
load_config "tzinor_node_Porto_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-Porto READY."
