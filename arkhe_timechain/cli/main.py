#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — CLI para gerenciamento do TemporalChain.
"""

import asyncio
import click
import json
import sys
from pathlib import Path

from ..core import TemporalChain, EventType

@click.group()
@click.option("--storage", default="sqlite", help="Backend de armazenamento")
@click.option("--config", default=None, help="Caminho para arquivo de configuração JSON")
@click.pass_context
def cli(ctx, storage: str, config: str):
    """Timechain CLI — Gerenciamento da cadeia temporal ARKHE."""
    ctx.ensure_object(dict)
    ctx.obj["storage"] = storage
    ctx.obj["config"] = json.loads(Path(config).read_text()) if config else {}

@cli.command()
@click.pass_context
def init(ctx):
    """Inicializa nova cadeia temporal."""
    async def _init():
        tc = TemporalChain(
            storage_backend=ctx.obj["storage"],
            storage_config=ctx.obj["config"],
        )
        # Ancorar evento de gênese
        await tc.anchor_event(
            event_type=EventType.CUSTOM,
            payload={"action": "chain_init", "version": "1.0.0"},
            metadata={"initialized_by": "cli"},
        )
        click.echo(f"✅ Cadeia inicializada. Selo de gênese: {tc._genesis_seal[:16]}...")
        click.echo(f"📍 Path: {tc.storage.db_path if hasattr(tc.storage, 'db_path') else 'in-memory'}")

    asyncio.run(_init())

@cli.command()
@click.argument("event_type")
@click.option("--payload", "-p", required=True, help="Payload JSON do evento")
@click.option("--metadata", "-m", default="{}", help="Metadados JSON opcionais")
@click.option("--depends-on", "-d", multiple=True, help="IDs de eventos dependentes")
@click.pass_context
def anchor(ctx, event_type: str, payload: str, metadata: str, depends_on: tuple):
    """Ancora um novo evento na cadeia."""
    async def _anchor():
        tc = TemporalChain(
            storage_backend=ctx.obj["storage"],
            storage_config=ctx.obj["config"],
        )

        anchor = await tc.anchor_event(
            event_type=event_type,
            payload=json.loads(payload),
            metadata=json.loads(metadata),
            causal_deps=list(depends_on),
        )

        click.echo(f"✅ Evento ancorado:")
        click.echo(f"   ID: {anchor.event.event_id}")
        click.echo(f"   Selo: {anchor.event.seal[:16]}...")
        click.echo(f"   Posição: {anchor.position}")
        click.echo(f"   Cadeia: {anchor.chain_seal[:16]}...")

    asyncio.run(_anchor())

@cli.command()
@click.option("--event-id", help="Filtrar por ID do evento")
@click.option("--seal", help="Filtrar por selo do evento")
@click.option("--type", "-t", help="Filtrar por tipo de evento")
@click.option("--limit", "-l", default=10, help="Número máximo de resultados")
@click.pass_context
def query(ctx, event_id: str, seal: str, type: str, limit: int):
    """Consulta eventos na cadeia."""
    async def _query():
        tc = TemporalChain(
            storage_backend=ctx.obj["storage"],
            storage_config=ctx.obj["config"],
        )

        if event_id:
            event = await tc.get_event_by_id(event_id)
            if event:
                click.echo(json.dumps(event.to_dict(), indent=2, default=str))
            else:
                click.echo("❌ Evento não encontrado", err=True)
                sys.exit(1)
        elif seal:
            event = await tc.get_event_by_seal(seal)
            if event:
                click.echo(json.dumps(event.to_dict(), indent=2, default=str))
            else:
                click.echo("❌ Selo não encontrado", err=True)
                sys.exit(1)
        else:
            events = await tc.query_events(event_type=type, limit=limit)
            for e in events:
                click.echo(f"{e.timestamp:.0f} [{e.event_type.value}] {e.event_id[:12]}... {e.seal[:8]}...")

    asyncio.run(_query())

@cli.command()
@click.option("--from-pos", default=0, help="Posição inicial para verificação")
@click.pass_context
def verify(ctx, from_pos: int):
    """Verifica integridade da cadeia."""
    async def _verify():
        tc = TemporalChain(
            storage_backend=ctx.obj["storage"],
            storage_config=ctx.obj["config"],
        )

        valid = await tc.verify_chain(from_pos)
        if valid:
            click.echo("✅ Cadeia íntegra")
            click.echo(f"   Eventos: {tc.event_count}")
            click.echo(f"   Selo atual: {tc.current_seal[:16]}...")
            click.echo(f"   Raiz Merkle: {tc.merkle_root[:16] + '...' if tc.merkle_root else 'N/A'}")
        else:
            click.echo("❌ Cadeia corrompida!", err=True)
            sys.exit(1)

    asyncio.run(_verify())

@cli.command()
@click.option("--start", default=0, help="Posição inicial")
@click.option("--end", default=None, help="Posição final (opcional)")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "binary"]))
@click.option("--output", "-o", help="Arquivo de saída (stdout se omitido)")
@click.pass_context
def export(ctx, start: int, end: int, format: str, output: str):
    """Exporta cadeia para auditoria externa."""
    async def _export():
        tc = TemporalChain(
            storage_backend=ctx.obj["storage"],
            storage_config=ctx.obj["config"],
        )

        content = await tc.export_chain(start, end, format)

        if output:
            Path(output).write_bytes(content if format == "binary" else content.encode())
            click.echo(f"✅ Exportado para {output}")
        else:
            if format == "json":
                click.echo(content)
            else:
                sys.stdout.buffer.write(content)

    asyncio.run(_export())

if __name__ == "__main__":
    cli(obj={})
