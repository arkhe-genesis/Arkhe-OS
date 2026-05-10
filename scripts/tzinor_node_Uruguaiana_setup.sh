#!/bin/bash
# Setup script for TZ-Uruguaiana
echo "Configuring TZ-Uruguaiana on channel C23..."
load_config "tzinor_node_Uruguaiana_config.json"
set_modulation PAM4_BIO_PHASE
echo "Node TZ-Uruguaiana READY."
