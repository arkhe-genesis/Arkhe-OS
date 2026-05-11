#!/usr/bin/env python3
"""
cli.py — CLI para pip-sovereign: gestão segura de pacotes Python.
"""
import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional

from .installer import install_package, install_requirements
from .verifier import verify_package_integrity
from .registry import SovereignRegistryClient
from .coherence_monitor import DependencyCoherenceMonitor
from .audit import record_installation

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pip-sovereign",
        description="ARKHE OS Sovereign Pip — Instalação segura e verificada de pacotes Python",
        epilog="Cada pacote é verificado, assinado e registrado. Φ_C é a moeda de confiança."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # install
    install_p = subparsers.add_parser("install", help="Instalar pacote(s) com verificação soberana")
    install_p.add_argument("packages", nargs="+", help="Pacotes no formato nome==versão ou nome>=versão")
    install_p.add_argument("-r", "--requirements", help="Arquivo requirements.txt para instalação em lote")
    install_p.add_argument("--no-cache", action="store_true", help="Não usar cache IPFS")
    install_p.add_argument("--dry-run", action="store_true", help="Simular instalação sem executar")
    install_p.add_argument("--tee", action="store_true", help="Executar instalação em enclave TEE")

    # verify
    verify_p = subparsers.add_parser("verify", help="Verificar integridade de pacote instalado")
    verify_p.add_argument("package", help="Nome do pacote a verificar")
    verify_p.add_argument("--full", action="store_true", help="Verificação completa incluindo dependências")

    # search
    search_p = subparsers.add_parser("search", help="Buscar pacotes no registry soberano")
    search_p.add_argument("query", help="Termo de busca")
    search_p.add_argument("--min-phi-rep", type=float, default=0.7, help="Reputação mínima do mantenedor")

    # publish
    publish_p = subparsers.add_parser("publish", help="Publicar pacote no registry soberano")
    publish_p.add_argument("dist_path", help="Caminho para distribuição (.whl ou .tar.gz)")
    publish_p.add_argument("--sign", action="store_true", help="Assinar pacote com chave do mantenedor")
    publish_p.add_argument("--kym-proof", help="Prova KYM do mantenedor")

    # audit
    audit_p = subparsers.add_parser("audit", help="Auditar instalações e dependências")
    audit_p.add_argument("--package", help="Auditar pacote específico")
    audit_p.add_argument("--environment", help="Auditar ambiente virtual inteiro")
    audit_p.add_argument("--export", help="Exportar relatório de auditoria")

    # coherence
    coh_p = subparsers.add_parser("coherence", help="Analisar coerência de dependências")
    coh_p.add_argument("requirements_file", help="Arquivo requirements.txt a analisar")
    coh_p.add_argument("--suggest", action="store_true", help="Sugerir alternativas mais coerentes")

    # config
    config_p = subparsers.add_parser("config", help="Gerenciar configuração do pip-sovereign")
    config_p.add_argument("--show", action="store_true", help="Mostrar configuração atual")
    config_p.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), action="append", help="Definir configuração")

    return parser

def cmd_install(args) -> int:
    """Executar comando install."""
    if args.requirements:
        return install_requirements(
            requirements_path=Path(args.requirements),
            no_cache=args.no_cache,
            dry_run=args.dry_run,
            use_tee=args.tee
        )

    for pkg_spec in args.packages:
        name, version = _parse_package_spec(pkg_spec)
        result = install_package(
            package_name=name,
            version=version,
            no_cache=args.no_cache,
            dry_run=args.dry_run,
            use_tee=args.tee
        )
        if not result["success"]:
            print(f"❌ Falha ao instalar {name}: {result.get('error')}")
            return 1
        record_installation(result)
    return 0

def cmd_verify(args) -> int:
    """Executar comando verify."""
    result = verify_package_integrity(args.package, full_check=args.full)
    if result["valid"]:
        print(f"✅ {args.package} verificado: {result['message']}")
        return 0
    else:
        print(f"❌ {args.package} falhou na verificação: {result['message']}")
        return 1

def cmd_search(args) -> int:
    """Executar comando search."""
    registry = SovereignRegistryClient()
    results = registry.search(args.query, min_phi_rep=args.min_phi_rep)

    if not results:
        print(f"⚠️  Nenhum pacote encontrado para '{args.query}' com Φ-REP ≥ {args.min_phi_rep}")
        return 0

    print(f"📦 Resultados para '{args.query}':\n")
    for pkg in results[:10]:  # Top 10
        print(f"  • {pkg['name']}=={pkg['version']}")
        print(f"    Φ-REP: {pkg['phi_rep']:.2f} | Mantenedor: {pkg['maintainer'][:16]}...")
        print(f"    Hash: {pkg['hash_sha3_256'][:16]}...")
        if pkg.get("coherence_score"):
            print(f"    Φ_C: {pkg['coherence_score']:.3f}")
        print()
    return 0

def cmd_publish(args) -> int:
    """Executar comando publish."""
    from .publisher import publish_package
    result = publish_package(
        dist_path=Path(args.dist_path),
        sign_package=args.sign,
        kym_proof=args.kym_proof
    )
    if result["success"]:
        print(f"✅ Pacote publicado: {result['package_name']}=={result['version']}")
        print(f"   IPFS CID: {result['ipfs_cid']}")
        print(f"   Registry URL: {result['registry_url']}")
        return 0
    else:
        print(f"❌ Falha ao publicar: {result.get('error')}")
        return 1

def cmd_audit(args) -> int:
    """Executar comando audit."""
    from .audit import run_audit
    report = run_audit(
        package_name=args.package,
        environment=args.environment,
        export_path=args.export
    )

    print(f"📊 Relatório de Auditoria")
    print(f"   Pacotes verificados: {report['packages_checked']}")
    print(f"   Dependências analisadas: {report['dependencies_analyzed']}")
    print(f"   Problemas encontrados: {len(report['issues'])}")

    if report["issues"]:
        print("\n⚠️  Problemas:")
        for issue in report["issues"]:
            print(f"   • {issue['severity']}: {issue['message']}")

    if args.export:
        print(f"\n📄 Relatório exportado para: {args.export}")

    return 0 if not report["issues"] else 1

def cmd_coherence(args) -> int:
    """Executar comando coherence."""
    monitor = DependencyCoherenceMonitor()
    analysis = monitor.analyze_requirements(Path(args.requirements_file))

    print(f"🧠 Análise de Coerência: {args.requirements_file}")
    print(f"   Pacotes: {analysis['total_packages']}")
    print(f"   Φ_C médio: {analysis['avg_coherence']:.3f}")
    print(f"   Risco estimado: {analysis['risk_level']}")

    if analysis["low_coherence_packages"]:
        print(f"\n⚠️  Pacotes com baixa coerência:")
        for pkg in analysis["low_coherence_packages"]:
            print(f"   • {pkg['name']}: Φ_C={pkg['coherence']:.3f}")

    if args.suggest and analysis["suggestions"]:
        print(f"\n💡 Sugestões de alternativas mais coerentes:")
        for suggestion in analysis["suggestions"]:
            print(f"   • Substituir {suggestion['current']} por {suggestion['alternative']}")
            print(f"     Ganho estimado de Φ_C: +{suggestion['coherence_gain']:.3f}")

    return 0 if analysis["risk_level"] != "high" else 1

def cmd_config(args) -> int:
    """Executar comando config."""
    from .config import SovereignPipConfig

    config = SovereignPipConfig.load()

    if args.show:
        print("📋 Configuração atual do pip-sovereign:")
        print(json.dumps(config.to_dict(), indent=2))
        return 0

    if args.set:
        for key, value in args.set:
            config.set(key, value)
            print(f"✅ {key} = {value}")
        config.save()
        print("📝 Configuração salva")
        return 0

    return 1

def _parse_package_spec(spec: str) -> tuple[str, Optional[str]]:
    """Parse package specification like 'requests==2.28.0' or 'numpy>=1.24'."""
    import re
    match = re.match(r'^([a-zA-Z0-9_-]+)([=<>!~]+.+)?$', spec.strip())
    if not match:
        raise ValueError(f"Invalid package spec: {spec}")
    name = match.group(1)
    version_spec = match.group(2)
    # Extract exact version if == is used
    if version_spec and version_spec.startswith("=="):
        return name, version_spec[2:]
    return name, None

def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for pip-sovereign CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    commands = {
        "install": cmd_install,
        "verify": cmd_verify,
        "search": cmd_search,
        "publish": cmd_publish,
        "audit": cmd_audit,
        "coherence": cmd_coherence,
        "config": cmd_config,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            return handler(args)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 2
    return 1

if __name__ == "__main__":
    sys.exit(main())