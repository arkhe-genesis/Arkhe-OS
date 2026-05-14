#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli_integration.py — Comandos CLI para Mythos Gate

Adiciona comandos:
• arkp publish --ethical-review — Força avaliação ética mesmo para baixo risco
• arkp mythos status <package> — Mostra avaliação ética de pacote
• arkp mythos review — Interface para revisores humanos
"""

import argparse
import asyncio
import time
from pathlib import Path
from .mythos_publisher import MythosGatePublisher, PublicationDecision

async def cmd_publish_with_mythos(args, publisher: MythosGatePublisher, arkp_cli):
    """Comando: arkp publish com avaliação Mythos Gate integrada."""
    # Carregar manifesto e código (mesmo fluxo do publish normal)
    manifest = load_manifest()  # Função existente do arkp
    source_files = collect_source_files()  # Função existente

    # Avaliar via Mythos Gate
    can_publish, message, assessment = await publisher.evaluate_for_publication(
        manifest=manifest,
        source_files=source_files,
        dependencies=manifest.get("dependencies", {}),
        author_orcid=args.author,
    )

    if not can_publish:
        print(message)
        if assessment and assessment.decision == PublicationDecision.REQUIRES_REVIEW:
            print(f"\n📬 Revisores notificados. Aguardando aprovação...")
            print(f"   Prazo: 72 horas")
            print(f"   Seal: {assessment.mythos_seal[:16]}...")
        return False

    # Se aprovado, prosseguir com publicação normal
    print(message)
    return await arkp_cli.publish(
        name=manifest["package"]["name"],
        code="",  # Já coletado
        author_orcid=args.author,
    )

def cmd_mythos_status(args, publisher: MythosGatePublisher):
    """Comando: arkp mythos status <package>[@version]"""
    package_spec = args.package
    if "@" in package_spec:
        name, version = package_spec.split("@", 1)
    else:
        name = package_spec
        version = None

    assessment = publisher.get_assessment(name, version or "latest")

    if not assessment:
        print(f"❌ No ethical assessment found for {package_spec}")
        return

    print(f"🔍 Ethical Assessment — {assessment.package_name}@{assessment.package_version}")
    print(f"   Decision: {assessment.decision.value.upper()}")
    print(f"   Risk Score: {assessment.overall_risk_score:.3f}")
    print(f"   Rationale: {assessment.rationale}")
    print(f"   Mythos Seal: {assessment.mythos_seal}")
    print(f"   Timestamp: {time.ctime(assessment.timestamp)}")

    if assessment.risk_breakdown:
        print(f"\n   Risk Breakdown:")
        for category, score in assessment.risk_breakdown.items():
            if score > 0.1:
                print(f"     • {category.value}: {score:.3f}")

    if assessment.recommendations:
        print(f"\n   Recommendations:")
        for rec in assessment.recommendations:
            print(f"     • {rec}")

def register_mythos_commands(subparsers, publisher: MythosGatePublisher, arkp_cli):
    """Registra comandos Mythos no arkp CLI."""
    # Modificar comando publish existente para suportar --ethical-review
    # (Isso requer modificar o parser principal do arkp)

    # Novo subcomando mythos
    mythos_parser = subparsers.add_parser("mythos", help="Mythos Gate ethical review tools")
    mythos_sub = mythos_parser.add_subparsers(dest="mythos_cmd")

    # status
    status_p = mythos_sub.add_parser("status", help="Show ethical assessment of a package")
    status_p.add_argument("package", help="Package name[@version]")
    status_p.set_defaults(func=lambda args: cmd_mythos_status(args, publisher))

    # review (para revisores humanos)
    review_p = mythos_sub.add_parser("review", help="Review pending package assessments")
    review_p.set_defaults(func=lambda args: cmd_mythos_review(args, publisher))

async def cmd_mythos_review(args, publisher: MythosGatePublisher):
    """Interface simplificada para revisores humanos."""
    print("👁️  Mythos Gate — Pending Reviews")
    print("   (Em produção: interface web ou notificação por email)")
    print("   Aqui: listando avaliações pendentes...")

    # Em produção: consultar ledger por avaliações com status REQUIRES_REVIEW
    print("   No pending reviews at this time.")
