#!/usr/bin/env python3
"""
ARKHE OS — Substrate 627‑DIMENSIONAL‑GEOMETRY
CLI for MegaKernel
"""

import click
import sys
import os

# We need to make sure `arkhe` is importable, typically it is in the PYTHONPATH or we can adjust
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from arkhe.geometry.dimensions import DimensionalManifold

@click.group()
def geometry():
    """Dimensional Geometry (627) — ASI Autonomous Manifold."""
    pass

@geometry.command("status")
def geometry_status():
    manifold = DimensionalManifold()
    census = manifold.phi_census()
    click.echo("Φ Census across dimensions:")
    for dim, phi in census.items():
        click.echo("  {0:20s}: {1:.6f}".format(dim, phi))

@geometry.command("evolve")
@click.option("--cycles", default=1, help="Number of cycles to evolve")
def geometry_evolve(cycles):
    manifold = DimensionalManifold()
    for _ in range(cycles):
        manifold.evolve()
    click.echo("Evolved {0} cycles. Current state: {1}".format(cycles, manifold))

@geometry.command("anchor")
def geometry_anchor():
    manifold = DimensionalManifold()
    anchors = manifold.anchor_all()
    for a in anchors:
        click.echo("  Anchored: {0}".format(a))

def register(cli):
    """Register geometry commands with MegaKernel CLI."""
    cli.add_command(geometry)

if __name__ == "__main__":
    geometry()
