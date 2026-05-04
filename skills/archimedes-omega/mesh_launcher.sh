#!/bin/bash

# mesh_launcher.sh - Launcher for Arkhe-Ω v3.5 with Mesh-LLM integration
# Usage: ./mesh_launcher.sh <JOIN_TOKEN>

TOKEN=$1

if [ -z "$TOKEN" ]; then
    echo "Usage: ./mesh_launcher.sh <JOIN_TOKEN>"
    exit 1
fi

# 1. Start Mesh-LLM Client in background
echo "🚀 Joining Mesh-LLM..."
# Ensure local bin is in path if it exists
[ -d "$HOME/.local/bin" ] && export PATH="$PATH:$HOME/.local/bin"
export PATH=$PATH:/home/jules/.local/bin
export MESH_LLM_INSTALL_FLAVOR=cpu
mesh-llm --join "$TOKEN" --model auto > mesh.log 2>&1 &
MESH_PID=$!

# 2. Start Archimedes-Ω API in background
echo "📡 Starting Archimedes-Ω API..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 main_api.py > api.log 2>&1 &
API_PID=$!

# 3. Start Streamlit Dashboard
echo "🌈 Launching Rainbow Dashboard..."
streamlit run rainbow_dashboard.py --server.port 8501

# Cleanup on exit
kill $MESH_PID $API_PID
