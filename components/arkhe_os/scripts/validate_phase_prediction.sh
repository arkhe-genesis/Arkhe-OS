#!/bin/bash
echo "🔬 Validating phase prediction..."
if [ -f "/tmp/arkhe/phase_validation.json" ]; then
    cat "/tmp/arkhe/phase_validation.json"
else
    echo "Report not found."
fi
