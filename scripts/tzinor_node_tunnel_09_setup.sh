#!/bin/bash
# Setup script for TZ-tunnel_09
echo "Configuring TZ-tunnel_09 on channel C34..."
load_config "tzinor_node_tunnel_09_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-tunnel_09 READY."
