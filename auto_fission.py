#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_fission.py — Executor de Fissão Canônica Automática
Canon: ∞.Ω.∇+++.319.auto_fission

Executa automaticamente a reorganização sugerida pelo check_137_rule.py,
com confirmação do usuário, backup atômico e ancoragem na TemporalChain.

Uso:
    python auto_fission.py <violation_report.json> [--dry-run] [--force]
"""

import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('auto_fission.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constantes canônicas
ALPHA_INV = 137.035999084
CANON = "∞.Ω.∇+++.319.auto_fission"
TEMPORAL_CHAIN_ENDPOINT = "https://temporal.arkhe.org/v1/anchor"


def load_violation_report(report_path: str) -> Dict:
    """Carrega relatório de violação do check_137_rule.py."""
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_backup_path(original_path: Path) -> Path:
    """Gera caminho para backup atômico com timestamp canônico."""
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_name = f"{original_path.name}.backup.{timestamp}"
    return original_path.parent / backup_name


def create_atomic_backup(directory: Path) -> Path:
    """Cria backup atômico de diretório antes da fissão."""
    backup_path = generate_backup_path(directory)

    logger.info(f"📦 Criando backup atômico: {directory} → {backup_path}")

    # Usar shutil.copytree com dirs_exist_ok para Python 3.8+
    shutil.copytree(directory, backup_path, dirs_exist_ok=True)

    # Verificar integridade do backup via hash de manifesto
    manifest = generate_directory_manifest(directory)
    backup_manifest = generate_directory_manifest(backup_path)

    if manifest != backup_manifest:
        raise RuntimeError("❌ Backup integrity check failed!")

    logger.info(f"✅ Backup criado e verificado: {backup_path}")
    return backup_path


def generate_directory_manifest(directory: Path) -> str:
    """Gera hash SHA3-256 de manifesto de diretório para verificação."""
    items = []
    for item in sorted(directory.iterdir()):
        if item.name in {'.git', 'node_modules', '__pycache__', 'bin', 'obj'}:
            continue
        items.append(f"{item.name}:{item.stat().st_mtime}:{item.stat().st_size}")

    manifest_content = "\n".join(items)
    return hashlib.sha3_256(manifest_content.encode('utf-8')).hexdigest()


def execute_fission_plan(violation: Dict, dry_run: bool = False) -> bool:
    """Executa plano de fissão canônica para uma violação específica."""
    dir_path = Path(violation['path'])
    suggestions = violation.get('fission_suggestions', [])

    if not suggestions:
        logger.warning(f"⚠️  Nenhuma sugestão de fissão para {dir_path}")
        return False

    logger.info(f"🔧 Executando fissão canônica para: {dir_path}")
    logger.info(f"   Itens atuais: {violation['count']} | Limite: {violation['limit']}")

    if dry_run:
        logger.info("   [DRY-RUN] Nenhuma alteração será feita")
        for suggestion in suggestions:
            logger.info(f"   → {suggestion}")
        return True

    # Criar backup atômico antes de qualquer modificação
    backup_path = create_atomic_backup(dir_path)

    try:
        # Executar cada sugestão de fissão
        for suggestion in suggestions:
            # Parse da sugestão: "→ src/modules/cs/ — 45 itens"
            if "→" in suggestion and "—" in suggestion:
                parts = suggestion.strip().split("→")[1].split("—")
                target_path = parts[0].strip()

                # Criar subdiretório se não existir
                full_target = dir_path / target_path
                full_target.mkdir(parents=True, exist_ok=True)
                logger.info(f"   ✅ Criado: {full_target}")

                # Mover itens correspondentes (lógica simplificada)
                # Em produção: implementar lógica completa de agrupamento por extensão/prefixo
                items_to_move = identify_items_for_fission(dir_path, target_path)
                for item in items_to_move:
                    src = dir_path / item
                    dst = full_target / item
                    if src.exists() and not dst.exists():
                        shutil.move(str(src), str(dst))
                        logger.info(f"      ↪ {item}")

        # Verificar conformidade pós-fissão
        new_count = len([i for i in dir_path.iterdir() if i.name not in {'.git', 'node_modules', '__pycache__'}])
        if new_count <= violation['limit']:
            logger.info(f"✅ Fissão concluída: {new_count} itens (limite: {violation['limit']})")
            return True
        else:
            logger.error(f"❌ Fissão incompleta: {new_count} itens ainda excedem limite")
            return False

    except Exception as e:
        logger.error(f"❌ Erro durante fissão: {e}")
        # Rollback: restaurar do backup
        logger.info("🔄 Executando rollback...")
        if backup_path.exists():
            shutil.rmtree(dir_path)
            shutil.copytree(backup_path, dir_path)
            logger.info(f"✅ Rollback concluído: {dir_path} restaurado")
        return False


def identify_items_for_fission(directory: Path, target_subdir: str) -> List[str]:
    """Identifica itens que devem ser movidos para subdiretório de fissão."""
    # Lógica simplificada: agrupar por extensão ou prefixo
    items = []
    target_name = target_subdir.rstrip('/').split('/')[-1]

    for item in directory.iterdir():
        if item.name in {'.git', 'node_modules', '__pycache__', 'bin', 'obj', target_name}:
            continue
        if item.is_file():
            # Agrupar por extensão
            ext = item.suffix.lstrip('.').lower() or 'no_ext'
            if ext == target_name or target_name in ['cs', 'py', 'rs', 'js', 'json', 'yaml']:
                if ext == target_name:
                    items.append(item.name)
        elif item.is_dir():
            # Agrupar por prefixo alfabético de 2 caracteres
            prefix = item.name[:2].lower()
            if prefix == target_name:
                items.append(item.name)

    return items


def anchor_fission_to_temporal_chain(violation: Dict, success: bool, backup_path: Optional[Path]) -> str:
    """Ancora resultado da fissão na TemporalChain."""
    payload = {
        "canon": CANON,
        "event_type": "auto_fission_executed",
        "directory": str(violation['path']),
        "original_count": violation['count'],
        "limit": violation['limit'],
        "success": success,
        "backup_path": str(backup_path) if backup_path else None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "architect": "orcid:0009-0005-2697-4668"
    }

    # Calcular selo canônico SHA3-256
    seal_input = json.dumps(payload, sort_keys=True).encode('utf-8')
    canonical_seal = hashlib.sha3_256(seal_input).hexdigest()

    # Mock: em produção, POST para TEMPORAL_CHAIN_ENDPOINT
    logger.info(f"🔗 Ancorando na TemporalChain: {canonical_seal[:32]}...")

    return canonical_seal


def confirm_execution(violations: List[Dict], dry_run: bool) -> bool:
    """Solicita confirmação do usuário antes de executar fissão."""
    if dry_run:
        logger.info("🔍 Modo DRY-RUN: nenhuma alteração será feita")
        return True

    print(f"\n⚠️  CONFIRMAÇÃO DE FISSÃO CANÔNICA")
    print(f"   {len(violations)} diretório(s) violam a Regra dos 137")
    print(f"   Alpha⁻¹ = {ALPHA_INV:.9f}")
    print()

    for i, v in enumerate(violations, 1):
        print(f"   {i}. {v['path']}")
        print(f"      • Itens: {v['count']} (excesso: {v['count'] - v['limit']})")
        if v.get('fission_suggestions'):
            print(f"      • Sugestões:")
            for s in v['fission_suggestions'][:3]:  # Mostrar primeiras 3
                print(f"        {s}")
            if len(v['fission_suggestions']) > 3:
                print(f"        ... e mais {len(v['fission_suggestions']) - 3}")
        print()

    response = input("Executar fissão canônica? [y/N]: ").strip().lower()
    return response in ['y', 'yes', 'sim']


def main():
    parser = argparse.ArgumentParser(
        description="Auto-Fission Canônica — Executa reorganização sugerida pelo check_137_rule.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Canon: {CANON}
Alpha⁻¹: {ALPHA_INV:.9f}

Exemplos:
  python auto_fission.py violations.json --dry-run
  python auto_fission.py violations.json --force  # Pula confirmação
        """
    )
    parser.add_argument("report", help="Caminho para relatório JSON do check_137_rule.py")
    parser.add_argument("--dry-run", action="store_true", help="Simular sem executar alterações")
    parser.add_argument("--force", "-f", action="store_true", help="Executar sem confirmação")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output detalhado")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"🏛️ ARKHE Ω‑TEMP v∞.Ω — Substrate 319: Auto-Fission")
    logger.info(f"   Canon: {CANON}")
    logger.info(f"   Alpha⁻¹: {ALPHA_INV:.9f}")
    logger.info(f"   Report: {args.report}")
    if args.dry_run:
        logger.info("   ⚠️  DRY-RUN MODE")

    # Carregar relatório de violações
    try:
        report = load_violation_report(args.report)
        violations = report.get('violations', [])
    except Exception as e:
        logger.error(f"❌ Falha ao carregar relatório: {e}")
        return 1

    if not violations:
        logger.info("✅ Nenhum diretório viola a Regra dos 137 — nenhuma ação necessária")
        return 0

    logger.info(f"📋 {len(violations)} violação(ões) encontrada(s)")

    # Confirmar execução (a menos que --force ou --dry-run)
    if not args.force and not args.dry_run:
        if not confirm_execution(violations, args.dry_run):
            logger.info("❌ Fissão cancelada pelo usuário")
            return 0

    # Executar fissão para cada violação
    results = []
    for violation in violations:
        success = execute_fission_plan(violation, dry_run=args.dry_run)
        results.append({
            "path": violation['path'],
            "success": success,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        # Ancorar resultado na TemporalChain
        seal = anchor_fission_to_temporal_chain(
            violation,
            success,
            Path(generate_backup_path(Path(violation['path']))) if not args.dry_run else None
        )
        results[-1]["temporal_seal"] = seal

    # Relatório final
    success_count = sum(1 for r in results if r['success'])
    print(f"\n{'='*65}")
    print(f"  📊 RELATÓRIO DE AUTO-FISSION")
    print(f"{'='*65}")
    print(f"  Total: {len(results)} | Sucesso: {success_count} | Falha: {len(results) - success_count}")
    print(f"  Modo: {'DRY-RUN' if args.dry_run else 'EXECUÇÃO'}")
    print(f"  Selos Temporais: {len([r for r in results if r.get('temporal_seal')])}")
    print(f"{'='*65}\n")

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
