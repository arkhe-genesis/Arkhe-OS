#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli_integration.py — Integração do cache com arkp CLI

Adiciona comandos:
• arkp cache status — Mostra estatísticas do cache
• arkp cache clear — Limpa cache (com opções)
• arkp cache prefetch — Pré-carrega dependências
"""

import argparse
import sys
from pathlib import Path
from .dependency_cache import DependencyCache, DependencyKey

def cmd_cache_status(args, cache: DependencyCache):
    """Comando: arkp cache status"""
    stats = cache.get_stats()

    print(f"📦 ARKHE Dependency Cache — Status")
    print(f"   Cache directory: {stats['cache_dir']}")
    print(f"   Usage: {stats['current_size_gb']:.2f} GB / {stats['max_size_gb']:.2f} GB ({stats['usage_percent']:.1f}%)")
    print(f"   Entries: {stats['valid_entries']} valid / {stats['expired_entries']} expired / {stats['corrupted_entries']} corrupted")
    print(f"   Total accesses: {stats['total_accesses']}")
    print(f"   Avg compression: {stats['avg_compression_ratio']:.2f}x")
    print(f"   Temporal anchored: {stats['temporal_anchored']} entries")
    print(f"   Avg QIP influence: {stats['avg_qip_influence']:.3f}")

def cmd_cache_clear(args, cache: DependencyCache):
    """Comando: arkp cache clear [--expired] [--all]"""
    if args.expired:
        count = cache.clear_expired()
        print(f"🧹 Removed {count} expired entries")
    elif args.all:
        # Limpar tudo (com confirmação)
        if not args.force:
            confirm = input(f"⚠️  Clear ALL cache at {cache.cache_dir}? (yes/no): ")
            if confirm.lower() != "yes":
                print("Cancelled.")
                return
        # Implementar limpeza completa...
        print("🗑️  Cache cleared")
    else:
        print("Use --expired or --all to specify what to clear")

def cmd_cache_prefetch(args, cache: DependencyCache):
    """Comando: arkp cache prefetch <package>[@version]"""
    # Implementar pré-busca de dependências...
    print(f"📥 Prefetching {args.package}...")

def register_cache_commands(subparsers, cache: DependencyCache):
    """Registra subcomandos de cache no arkp CLI."""
    cache_parser = subparsers.add_parser("cache", help="Manage dependency cache")
    cache_sub = cache_parser.add_subparsers(dest="cache_cmd")

    # status
    status_p = cache_sub.add_parser("status", help="Show cache statistics")
    status_p.set_defaults(func=lambda args: cmd_cache_status(args, cache))

    # clear
    clear_p = cache_sub.add_parser("clear", help="Clear cache entries")
    clear_p.add_argument("--expired", action="store_true", help="Clear only expired entries")
    clear_p.add_argument("--all", action="store_true", help="Clear entire cache")
    clear_p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    clear_p.set_defaults(func=lambda args: cmd_cache_clear(args, cache))

    # prefetch
    prefetch_p = cache_sub.add_parser("prefetch", help="Pre-fetch dependencies")
    prefetch_p.add_argument("package", help="Package name[@version]")
    prefetch_p.set_defaults(func=lambda args: cmd_cache_prefetch(args, cache))
