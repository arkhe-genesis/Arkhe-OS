#!/bin/bash
# Setup script for TZ-tunnel_04
echo "Configuring TZ-tunnel_04 on channel C29..."
load_config "tzinor_node_tunnel_04_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_04 READY."
