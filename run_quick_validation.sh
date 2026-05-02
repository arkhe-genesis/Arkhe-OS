#!/bin/bash
# run_quick_validation.sh
# Quickly runs the integrated homeostasis validation pipeline.

echo "Running Quick Validation for Integrated Homeostasis (v327.2)..."
python3 run_integrated_homeostasis.py
if [ $? -eq 0 ]; then
    echo "Validation successful!"
else
    echo "Validation failed!"
fi
