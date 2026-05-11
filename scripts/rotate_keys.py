#!/usr/bin/env python3
"""
rotate_keys.py — CLI para rotação automática de chaves de integridade do ARKHE OS.

Uso:
  python scripts/rotate_keys.py rotate            # Rotaciona chave agora
  python scripts/rotate_keys.py rotate --period 2h # Período de transição de 2 horas
  python scripts/rotate_keys.py list               # Lista chaves e status
  python scripts/rotate_keys.py status             # Status resumido da rotação
  python scripts/rotate_keys.py generate           # Gera nova chave (sem rotacionar)
"""

import sys
import time
import argparse
from pathlib import Path

# Adicionar raiz do pacote ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arkhe_os._key_rotation import get_key_manager, IntegrityKey


def cmd_rotate(args):
    """Executa rotação de chave."""
    km = get_key_manager()
    period = args.period
    new_key, old_key = km.rotate_key(
        transition_period_seconds=period,
        comment=args.comment or "Rotação via CLI"
    )

    print("🔐 Rotação de chave concluída.")
    print(f"   Chave anterior: {old_key.key_id if old_key else 'Nenhuma (primeira chave)'}")
    print(f"   Nova chave:      {new_key.key_id}")
    print(f"   Período de transição: {period} segundos")
    print(f"   Status: {len(km.get_active_keys())} chave(s) ativa(s) para verificação")


def cmd_list(args):
    """Lista todas as chaves."""
    km = get_key_manager()
    keys = km.list_keys()

    if not keys:
        print("Nenhuma chave encontrada. Execute 'rotate_keys.py generate' para criar a primeira.")
        return

    print(f"{'KEY ID':<25} {'VÁLIDA':<8} {'ATIVA':<8} {'ASSINA':<8} {'VÁLIDA ATÉ':<20} {'COMENTÁRIO'}")
    print("-" * 100)
    for k in keys:
        valid = "✓" if k['is_valid_now'] else "✗"
        active = "✓" if k['is_active'] else "✗"
        signing = "✓" if k['is_current_signing_key'] else ""
        until = f"{k['valid_until']:.0f}" if k['valid_until'] else "∞"
        print(f"{k['key_id']:<25} {valid:<8} {active:<8} {signing:<8} {until:<20} {k['comment']}")


def cmd_status(args):
    """Exibe status resumido."""
    km = get_key_manager()
    status = km.get_rotation_status()
    print(f"Total de chaves: {status['total_keys']}")
    print(f"Chaves ativas:   {status['active_keys']}")
    print(f"Chave atual:      {status['current_signing_key_id'] or 'Nenhuma'}")
    print(f"Armazenamento:    {status['storage_path']}")


def cmd_generate(args):
    """Gera nova chave sem rotacionar (útil para bootstrap)."""
    km = get_key_manager()
    key = km.generate_key(comment=args.comment or "Geração manual")
    print(f"✅ Nova chave gerada: {key.key_id}")
    print(f"   Armazenada em: {km.storage_path}")
    print(f"   ⚠️  BACKUP DA CHAVE: {key.key_hex}")


def parse_duration(value: str) -> float:
    """Converte string de duração (ex: '1h', '30m', '3600') para segundos."""
    value = value.strip().lower()
    if value.endswith('h'):
        return float(value[:-1]) * 3600
    elif value.endswith('m'):
        return float(value[:-1]) * 60
    elif value.endswith('s'):
        return float(value[:-1])
    else:
        return float(value)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARKHE OS Key Rotation Manager")
    subparsers = parser.add_subparsers(dest='command', help='Comandos')

    # Comando: rotate
    p_rotate = subparsers.add_parser('rotate', help='Rotacionar chave de integridade')
    p_rotate.add_argument('--period', type=parse_duration, default=3600.0,
                          help='Período de transição (ex: 1h, 30m, 3600s)')
    p_rotate.add_argument('--comment', help='Comentário descritivo')

    # Comando: list
    p_list = subparsers.add_parser('list', help='Listar todas as chaves')

    # Comando: status
    p_status = subparsers.add_parser('status', help='Status resumido da rotação')

    # Comando: generate
    p_gen = subparsers.add_parser('generate', help='Gerar nova chave sem rotacionar')
    p_gen.add_argument('--comment', help='Comentário descritivo')

    args = parser.parse_args()

    if args.command == 'rotate':
        cmd_rotate(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command == 'generate':
        cmd_generate(args)
    else:
        parser.print_help()
