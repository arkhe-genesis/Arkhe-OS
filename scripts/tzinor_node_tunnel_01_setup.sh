#!/bin/bash
# Setup script for TZ-tunnel_01
echo "Configuring TZ-tunnel_01 on channel C26..."
load_config "tzinor_node_tunnel_01_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_01 READY."
