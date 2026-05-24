#!/usr/bin/env python3
"""
arkhe-nuclei-peek — Integração PEEK + Nuclei para caching inteligente de templates.
Arquiteto: ORCID 0009-0005-2697-4668
"""

import subprocess, json, yaml, re, os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional
import click

# Importa o ContextMap do plugin arkhe-peek
from .peek_bridge import ContextMap, Distiller, Cartographer

class NucleiTemplateCache:
    """Cache de templates Nuclei usando PEEK context map."""

    def __init__(self, cache_name: str = "nuclei-templates"):
        self.map = ContextMap(cache_name, budget_tokens=2048)
        self.nuclei_bin = os.environ.get("NUCLEI_BIN", "nuclei")
        self.templates_dir = os.environ.get("NUCLEI_TEMPLATES",
            str(Path.home() / "nuclei-templates"))

    def scan_with_cache(self, target: str,
                        severity: str = "critical,high,medium",
                        use_cache: bool = True) -> Dict:
        """Execute Nuclei scan usando cache de templates."""

        # 1. Selecionar templates relevantes do cache
        relevant_templates = []
        if use_cache:
            relevant_templates = self._get_cached_templates(target)

        # 2. Construir comando Nuclei
        cmd = [self.nuclei_bin, "-target", target, "-severity", severity]

        if relevant_templates:
            # Usar apenas templates cacheados
            template_list = ",".join(relevant_templates)
            cmd.extend(["-templates", template_list])
            click.echo("[NUCLEI-PEEK] Using {0} cached templates.".format(len(relevant_templates)))
        else:
            # Fallback: usar todos os templates
            cmd.extend(["-templates", self.templates_dir])
            click.echo("[NUCLEI-PEEK] No cache. Using full template set.")

        cmd.extend(["-json", "-silent"])

        # 3. Executar scan
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        findings = []
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                try:
                    findings.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        # 4. Atualizar cache com resultados
        if use_cache and findings:
            self._update_cache(target, findings)

        return {
            "target": target,
            "findings": findings,
            "templates_used": len(relevant_templates) if relevant_templates else "all",
            "total_findings": len(findings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_cached_templates(self, target: str) -> List[str]:
        """Recupera templates relevantes do context map."""
        templates = []
        for item in self.map.sections.get("domain_constants", []):
            # Extrai ID de template do formato: "[tpl] CVE-2024-XXXX -> target_pattern"
            if "[tpl]" in item and target in item:
                tpl_id = item.split("[tpl]")[1].split("->")[0].strip()
                templates.append(tpl_id)
        return templates

    def _update_cache(self, target: str, findings: List[Dict]):
        """Atualiza context map com templates que geraram findings."""
        # Extrair templates que produziram resultados
        successful_templates = set()
        for f in findings:
            tpl_id = f.get("template-id", "")
            if tpl_id:
                successful_templates.add(tpl_id)

        # Adicionar ao context map
        for tpl_id in successful_templates:
            entry = "[tpl] {0} -> {1}".format(tpl_id, target)
            if entry not in self.map.sections.get("domain_constants", []):
                self.map.add("domain_constants", entry)

        # Adicionar sumário de resultados
        summary = "[scan] {0}: {1} findings, {2} templates at {3}".format(target, len(findings), len(successful_templates), datetime.now(timezone.utc).isoformat())
        self.map.add("reusable_results", summary)


@click.group()
def nuclei():
    """Nuclei vulnerability scanner with PEEK template caching."""
    pass

@nuclei.command("scan")
@click.argument("target")
@click.option("--severity", default="critical,high,medium")
@click.option("--no-cache", is_flag=True, help="Disable PEEK template cache.")
def nuclei_scan(target: str, severity: str, no_cache: bool):
    """Run Nuclei scan with intelligent template caching."""
    cache = NucleiTemplateCache()
    result = cache.scan_with_cache(target, severity, use_cache=not no_cache)
    click.echo(json.dumps(result, indent=2))

@nuclei.command("cache-show")
def nuclei_cache_show():
    """Display the Nuclei template cache."""
    cache = NucleiTemplateCache()
    click.echo(cache.map.to_prompt())

@nuclei.command("cache-clear")
def nuclei_cache_clear():
    """Clear the Nuclei template cache."""
    cache = NucleiTemplateCache()
    for sec in cache.map.sections:
        cache.map.sections[sec].clear()
    cache.map._save()
    click.echo("✓ Nuclei template cache cleared.")


def register_commands() -> Dict[str, click.Command]:
    """Register Nuclei-PEEK commands with MegaKernel CLI."""
    return {
        "nuclei": nuclei,
        "nuclei-scan": nuclei_scan,
        "nuclei-cache-show": nuclei_cache_show,
        "nuclei-cache-clear": nuclei_cache_clear,
    }
