#!/bin/bash
# Setup script for TZ-Central
echo "Configuring TZ-Central on channel C21..."
load_config "tzinor_node_Central_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-Central READY."
