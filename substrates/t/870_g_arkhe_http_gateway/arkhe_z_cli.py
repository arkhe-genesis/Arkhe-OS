#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           ARKHE-Z CLI — Bridge Client (Substrato 870-G-CLI)                 ║
║    Comando: arkhe-z publish / arkhe-z verify / arkhe-z health               ║
╚══════════════════════════════════════════════════════════════════════════════╝

Uso:
  python arkhe_z_cli.py publish --substrate 870-B --sequence "110000010010100011001111101101011100" --format yaml
  python arkhe_z_cli.py verify --hash abc123...
  python arkhe_z_cli.py health
"""

import click
import requests
import json
import yaml
import sys

DEFAULT_BRIDGE = "http://localhost:8700"

@click.group()
@click.option("--bridge-url", default=DEFAULT_BRIDGE, help="URL do gateway ARKHE")
@click.pass_context
def cli(ctx, bridge_url):
    ctx.ensure_object(dict)
    ctx.obj["bridge"] = bridge_url

@cli.command()
@click.option("--substrate", required=True, type=click.Choice([
    "870-B", "865", "864", "863", "862", "861", "860", "859"
]), help="Substrato de origem")
@click.option("--sequence", default=None, help="Sequência binária Glosa 245 (36 bits)")
@click.option("--action", default="ANCHOR", type=click.Choice(["ANCHOR", "DECREE", "DEPLOY", "SIMULATE", "SCAN", "PROPOSE"]))
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), default="json")
@click.option("--payload-file", type=click.Path(exists=True), help="Arquivo JSON com payload adicional")
@click.pass_context
def publish(ctx, substrate, sequence, action, fmt, payload_file):
    """Publica um decreto no gateway ARKHE e exibe o receipt."""
    bridge = ctx.obj["bridge"]
    payload = {}
    if payload_file:
        with open(payload_file, "r") as f:
            payload = json.load(f)

    req = {
        "substrate": substrate,
        "action": action,
        "sequence": sequence,
        "metadata": {"glosa": "245", "n": 5, "k": 2, "auto_complement": True, "shift": 18},
        "payload": payload
    }

    try:
        resp = requests.post(("{}/publish").format(bridge), json=req, timeout=30)
        resp.raise_for_status()
        receipt = resp.json()
    except requests.exceptions.ConnectionError:
        click.echo(("🚨 Erro: Gateway ARKHE inacessível em {}").format(bridge))
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        click.echo(("🚨 Erro HTTP {}: {}").format(e.response.status_code, e.response.text))
        sys.exit(1)

    # Decreto canônico estruturado
    decree = {
        "substrate": receipt["substrate"],
        "action": receipt["action"],
        "tx_hash": receipt["tx_hash"],
        "seal": receipt["seal"],
        "sequence": sequence,
        "registry_index": receipt["registry_index"],
        "phi_c": receipt["phi_c"],
        "ghost_threshold": receipt["ghost_threshold"],
        "status": receipt["status"],
        "keeper": "ψ",
        "orcid": "0009-0005-2697-4668",
        "gateway": "870-G",
        "timestamp": receipt["metadata"]["timestamp"],
        "verification_url": receipt["verification_url"]
    }

    if fmt == "yaml":
        click.echo(yaml.dump(decree, allow_unicode=True, sort_keys=False, default_flow_style=False))
    else:
        click.echo(json.dumps(decree, indent=2, ensure_ascii=False))

@cli.command()
@click.option("--hash", "hash_str", required=True, help="Selo SHA3-256 a verificar (64 hex)")
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), default="json")
@click.pass_context
def verify(ctx, hash_str, fmt):
    """Verifica se um selo está ancorado no registro canônico."""
    bridge = ctx.obj["bridge"]
    h = hash_str.lower().strip()
    if h.startswith("0x"):
        h = h[2:]

    try:
        resp = requests.get(("{}/verify/{}").format(bridge, h), timeout=10)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.ConnectionError:
        click.echo(("🚨 Gateway inacessível em {}").format(bridge))
        sys.exit(1)

    if fmt == "yaml":
        click.echo(yaml.dump(result, allow_unicode=True, sort_keys=False))
    else:
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))

@cli.command()
@click.pass_context
def health(ctx):
    """Exibe status de saúde do gateway e métricas de coerência."""
    bridge = ctx.obj["bridge"]
    try:
        resp = requests.get(("{}/health").format(bridge), timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        click.echo(("🚨 Gateway inacessível em {}").format(bridge))
        sys.exit(1)

    click.echo(("╔{}╗").format('═'*76))
    click.echo(("║{:^76}║").format('ARKHE GATEWAY HEALTH'))
    click.echo(("╠{}╣").format('═'*76))
    click.echo(("║  Status:        {:<58} ║").format(data['status']))
    click.echo(("║  Gateway ID:    {:<58} ║").format(data['gateway']))
    click.echo(("║  Version:       {:<58} ║").format(data['version']))
    click.echo(("║  Φ_C (live):    {:<58.6f} ║").format(data['phi_c']))
    click.echo(("║  Registry:      {:<58} ║").format(data['registry_size']))
    click.echo(("║  Uptime:        {:<58.2f}s ║").format(data['uptime_seconds']))
    click.echo(("╠{}╣").format('═'*76))
    click.echo(("║  Substratos Integrados:{:<52} ║").format(''))
    for sid, info in data["substrates"].items():
        click.echo(("║    {:<6} {:<25} Φ_C={:.3f}  {:<20} ║").format(sid, info['name'], info['phi_c'], info['status']))
    click.echo(("╚{}╝").format('═'*76))

if __name__ == "__main__":
    cli()
