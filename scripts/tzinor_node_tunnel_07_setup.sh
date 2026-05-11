#!/bin/bash
# Setup script for TZ-tunnel_07
echo "Configuring TZ-tunnel_07 on channel C32..."
load_config "tzinor_node_tunnel_07_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_07 READY."
