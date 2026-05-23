#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
arkhe-peek — Context Map Cache for Long-Context ARKHE Agents.
Implements the PEEK framework (Gu et al., MIT/Stanford, 2026) as a MegaKernel plugin.
Arquiteto: ORCID 0009-0005-2697-4668
"""

__version__ = "1.0.0"
__description__ = "PEEK context map cache for ARKHE agents"
__author__ = "ORCID 0009-0005-2697-4668"

import json, time, hashlib, os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import click

# ============================================================================
# Context Map Core (PEEK-inspired)
# ============================================================================

class ContextMap:
    """Bounded, prompt-resident cache of orientation knowledge about an external context."""

    SECTION_PRIORITY = [
        "parsing_schema",      # Evicted first (cheap to rediscover)
        "reusable_results",    # Agent-derived computations
        "domain_constants",    # Exact numeric params, enums, thresholds
        "context_understanding", # Entity inventories, summaries
        "context_roadmap",     # Protected last (structural index)
    ]

    def __init__(self, context_name: str, budget_tokens: int = 1024):
        self.context_name = context_name
        self.budget_tokens = budget_tokens
        self.sections: Dict[str, List[str]] = {
            "context_roadmap": [],
            "context_understanding": [],
            "domain_constants": [],
            "parsing_schema": [],
            "reusable_results": [],
        }
        self._item_counter = 0
        self._load()

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimator (4 chars ≈ 1 token for English)."""
        return max(1, len(text) // 4)

    def total_tokens(self) -> int:
        return sum(self._estimate_tokens(item) for sec in self.sections.values() for item in sec)

    def add(self, section: str, content: str, evict: bool = True):
        if section in self.sections:
            self.sections[section].append(content)
            self._item_counter += 1
            if evict:
                self._evict()
            self._save()

    def replace(self, section: str, index: int, content: str):
        if section in self.sections and 0 <= index < len(self.sections[section]):
            self.sections[section][index] = content
            self._save()

    def delete(self, section: str, index: int):
        if section in self.sections and 0 <= index < len(self.sections[section]):
            del self.sections[section][index]
            self._save()

    def _evict(self):
        """Priority-based eviction: remove from lowest-priority sections first."""
        while self.total_tokens() > self.budget_tokens:
            evicted = False
            for sec in self.SECTION_PRIORITY:
                if self.sections[sec]:
                    self.sections[sec].pop(0)
                    evicted = True
                    break
            if not evicted:
                break  # All sections empty, cannot reduce further

    def to_prompt(self) -> str:
        """Render as a system prompt fragment."""
        lines = ["## CONTEXT MAP"]
        section_names = {
            "context_roadmap": "Context Roadmap (structural index)",
            "context_understanding": "Context Understanding (entities, summaries)",
            "domain_constants": "Domain Constants (exact params, enums, thresholds)",
            "parsing_schema": "Parsing Schema (format, delimiters)",
            "reusable_results": "Reusable Results (derived computations)",
        }
        for sec, entries in self.sections.items():
            if entries:
                lines.append("### {0}".format(section_names.get(sec, sec)))
                for i, entry in enumerate(entries):
                    lines.append("- [{0}-{1:04d}] {2}".format(sec[:2], i, entry))
        return "\n".join(lines)

    def _save_path(self) -> Path:
        return Path.home() / ".arkhe" / "peek" / "{0}.json".format(self.context_name)

    def _save(self):
        path = self._save_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "context_name": self.context_name,
            "budget_tokens": self.budget_tokens,
            "sections": self.sections,
            "item_counter": self._item_counter,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(data, indent=2))

    def _load(self):
        path = self._save_path()
        if path.exists():
            data = json.loads(path.read_text())
            self.sections = data.get("sections", self.sections)
            self._item_counter = data.get("item_counter", 0)

    def snapshot(self) -> Dict:
        return {
            "context_name": self.context_name,
            "total_tokens": self.total_tokens(),
            "budget_tokens": self.budget_tokens,
            "sections": {k: len(v) for k, v in self.sections.items()},
            "items": {k: v.copy() for k, v in self.sections.items()},
        }

# ============================================================================
# Distiller (analyzes agent trajectory)
# ============================================================================

class Distiller:
    """Analyzes agent execution traces and proposes map updates."""

    def analyze(self, trajectory: str, current_map: ContextMap,
                task_description: str = "") -> Dict:
        """Extract reusable orientation knowledge from an execution trace."""
        # In production, this would call an LLM with the PEEK Distiller prompt.
        # Here we implement heuristic extraction for demonstration.

        findings = {
            "diagnosis": "Heuristic analysis of trajectory.",
            "item_tags": {},
            "cache_candidates": [],
        }

        # Heuristic 1: Detect structural patterns
        if "section" in trajectory.lower() or "header" in trajectory.lower():
            findings["cache_candidates"].append({
                "section": "context_roadmap",
                "content": "[Auto] Structural pattern detected in {0}".format(task_description[:50]),
                "transferability": "Navigation",
                "rationale": "Agent spent iterations discovering document structure.",
            })

        # Heuristic 2: Detect domain constants (numbers, thresholds)
        import re
        numbers = re.findall(r'(?:threshold|limit|rate|constant)\s*[:=]\s*(\d+\.?\d*)',
                            trajectory, re.IGNORECASE)
        for num in numbers[:3]:
            findings["cache_candidates"].append({
                "section": "domain_constants",
                "content": "[Auto] Detected constant: {0}".format(num),
                "transferability": "Computation",
                "rationale": "Numeric constant found in trajectory.",
            })

        # Heuristic 3: Detect format/parsing patterns
        if "delimiter" in trajectory.lower() or "split" in trajectory.lower():
            findings["cache_candidates"].append({
                "section": "parsing_schema",
                "content": "[Auto] Parsing pattern observed in {0}".format(task_description[:50]),
                "transferability": "Parsing",
                "rationale": "Agent spent iterations on format discovery.",
            })

        return findings

# ============================================================================
# Cartographer (applies structured edits)
# ============================================================================

class Cartographer:
    """Translates Distiller output into map edit operations."""

    def apply(self, findings: Dict, current_map: ContextMap) -> int:
        """Apply findings to the context map. Returns number of changes."""
        changes = 0

        # Apply cache candidates
        for candidate in findings.get("cache_candidates", []):
            section = candidate.get("section", "context_understanding")
            content = candidate.get("content", "")
            if section in current_map.sections and content:
                # Check for duplicates
                if content not in current_map.sections[section]:
                    current_map.add(section, content)
                    changes += 1

        return changes

# ============================================================================
# CLI Commands
# ============================================================================

@click.group()
def peek():
    """PEEK context map cache for ARKHE agents."""
    pass

@peek.command("init")
@click.argument("context_name")
@click.option("--budget", default=1024, help="Token budget for the context map.")
def peek_init(context_name: str, budget: int):
    """Initialize a new context map for a recurring external context."""
    cm = ContextMap(context_name, budget)
    cm.add("context_roadmap", "Context map initialized for '{0}' at {1}".format(context_name, datetime.now(timezone.utc).isoformat()))
    click.echo("✓ Context map '{0}' initialized with {1} token budget.".format(context_name, budget))
    click.echo("  Path: {0}".format(cm._save_path()))

@peek.command("show")
@click.argument("context_name")
def peek_show(context_name: str):
    """Display the current context map."""
    cm = ContextMap(context_name)
    click.echo(cm.to_prompt())
    click.echo("\nTotal tokens: {0} / {1}".format(cm.total_tokens(), cm.budget_tokens))

@peek.command("update")
@click.argument("context_name")
@click.option("--trajectory", "-t", help="Path to agent execution trajectory file.")
@click.option("--task", help="Description of the task that was executed.")
def peek_update(context_name: str, trajectory: str, task: str):
    """Update the context map from an agent execution trajectory."""
    cm = ContextMap(context_name)

    traj_text = ""
    if trajectory:
        traj_path = Path(trajectory)
        if traj_path.exists():
            traj_text = traj_path.read_text()
    else:
        # Read from stdin if piped
        import sys
        if not sys.stdin.isatty():
            traj_text = sys.stdin.read()

    if not traj_text:
        click.echo("[ERROR] No trajectory provided. Use --trajectory or pipe input.", err=True)
        return

    distiller = Distiller()
    cartographer = Cartographer()

    click.echo("[PEEK] Analyzing trajectory for '{0}'...".format(context_name))
    findings = distiller.analyze(traj_text, cm, task or context_name)

    click.echo("[PEEK] Diagnosis: {0}".format(findings['diagnosis']))

    changes = cartographer.apply(findings, cm)
    click.echo("[PEEK] Applied {0} changes to context map.".format(changes))
    click.echo("[PEEK] Map size: {0} / {1} tokens.".format(cm.total_tokens(), cm.budget_tokens))

@peek.command("evict")
@click.argument("context_name")
@click.option("--target", default=None, type=int, help="Target token count (default: budget).")
def peek_evict(context_name: str, target: int):
    """Manually evict entries to meet token budget."""
    cm = ContextMap(context_name)
    before = cm.total_tokens()
    if target:
        old_budget = cm.budget_tokens
        cm.budget_tokens = target
        cm._evict()
        cm.budget_tokens = old_budget
    else:
        cm._evict()
    after = cm.total_tokens()
    click.echo("[PEEK] Evicted {0} tokens. Map: {1} / {2} tokens.".format(before - after, after, cm.budget_tokens))

@peek.command("export")
@click.argument("context_name")
@click.option("--format", "fmt", type=click.Choice(["json", "prompt", "both"]), default="prompt")
def peek_export(context_name: str, fmt: str):
    """Export the context map in various formats."""
    cm = ContextMap(context_name)
    if fmt in ("prompt", "both"):
        click.echo(cm.to_prompt())
    if fmt in ("json", "both"):
        click.echo(json.dumps(cm.snapshot(), indent=2))

# ============================================================================
# Plugin registration for MegaKernel
# ============================================================================

def register_commands() -> Dict[str, click.Command]:
    """Register PEEK commands with the MegaKernel CLI."""
    return {
        "peek": peek,
        "peek-init": peek_init,
        "peek-show": peek_show,
        "peek-update": peek_update,
        "peek-evict": peek_evict,
        "peek-export": peek_export,
    }
