#!/bin/bash
# Setup script for TZ-tunnel_05
echo "Configuring TZ-tunnel_05 on channel C30..."
load_config "tzinor_node_tunnel_05_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_05 READY."
