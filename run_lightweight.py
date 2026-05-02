#!/usr/bin/env python3
"""
run_lightweight.py
Executor otimizado para CI do pipeline Crystal Brain.
"""
import os
import sys
import logging
import importlib.util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Executando pipeline em modo lightweight para CI...")

    spec = importlib.util.spec_from_file_location("arkhe_prod", "arkhe_v327.7_production_homeostasis.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    run_production_homeostasis = mod.run_production_homeostasis

    try:
        results = run_production_homeostasis(
            data_path='data/crystal_brain_v15',
            expected_hash='4d73343d058e76566d3aad241df439443412a856fdf62a1cd9233665f747129d',
            max_epochs=1,
            N_steps=100,
            capture_threshold=0.80,
            security_bits=40,
            output_dir='results/production_ci'
        )
        logger.info("CI Validation OK")
        sys.exit(0)
    except Exception as e:
        logger.error(f"CI Validation FAILED: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
