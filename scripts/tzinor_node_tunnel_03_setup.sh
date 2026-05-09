#!/bin/bash
# Setup script for TZ-tunnel_03
echo "Configuring TZ-tunnel_03 on channel C28..."
load_config "tzinor_node_tunnel_03_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_03 READY."
