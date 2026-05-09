#!/bin/bash
# Setup script for TZ-tunnel_06
echo "Configuring TZ-tunnel_06 on channel C31..."
load_config "tzinor_node_tunnel_06_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_06 READY."
