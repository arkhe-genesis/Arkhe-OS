#!/bin/bash
# Setup script for TZ-tunnel_08
echo "Configuring TZ-tunnel_08 on channel C33..."
load_config "tzinor_node_tunnel_08_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_08 READY."
