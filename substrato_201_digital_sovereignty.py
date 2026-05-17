#!/usr/bin/env python3
"""
ARKHE OS Substrato 201: Digital Sovereignty Framework Execution
Canon: ∞.Ω.∇+++.201
"""

import asyncio
from sovereignty.digital_sovereignty_core import DigitalSovereigntyFramework

async def main():
    print("==========================================================================")
    print(" ARKHE Ω‑TEMP v∞.Ω — SUBSTRATO 201: SOBERANIA DIGITAL ")
    print("==========================================================================")

    framework = DigitalSovereigntyFramework()

    print("\nExecutando Auditoria de Soberania Digital...")
    report = await framework.audit_sovereignty()

    print("\n--------------------------------------------------------------------------")
    print(f"Status: {report['sovereignty_status']}")
    print(f"Φ_C Soberano: {report['sovereignty_phi_c']:.4f}")
    print("--------------------------------------------------------------------------")

    print("\nDetalhes por Princípio:")
    for principle, details in report['details'].items():
        print(f" - {principle}:")
        print(f"   Score: {details['compliance_score']*100:.1f}%")
        print(f"   Métrica: {details['evidence']['metric']} ({details['evidence']['observed_value']:.1f} {details['evidence']['unit']})")
        if details['violations']:
            print(f"   Violações: {details['violations']}")

    print("\n--------------------------------------------------------------------------")
    print("Recomendações:")
    for rec in report['recommendations']:
        print(f" - {rec}")
    print("--------------------------------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
