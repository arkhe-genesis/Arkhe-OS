#!/bin/bash
# Setup script for TZ-tunnel_02
echo "Configuring TZ-tunnel_02 on channel C27..."
load_config "tzinor_node_tunnel_02_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_02 READY."
