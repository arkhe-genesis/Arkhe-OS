#!/usr/bin/env python3
import asyncio
from regional_expansion.custom_region_simulator import main_expansion_demo
from firmware.phi_c_link_calculator import main_firmware_demo
from production.top_secret_deploy import main_top_secret_demo

async def run_all():
    print("="*80)
    print("Iniciando demonstrações dos módulos base (Substrato 293)")
    print("="*80)

    main_expansion_demo()
    print("\n")
    main_firmware_demo()
    print("\n")
    await main_top_secret_demo()

if __name__ == "__main__":
    asyncio.run(run_all())
