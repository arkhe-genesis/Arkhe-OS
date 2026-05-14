#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
substrato_172_omega.py — Substrato 172-OMEGA (O Guardião Atratora) v2
Combina FortifiedExorcist, AttractorField, ExorcismCache, DomainProfiles e TemporalAudit.
"""

from src.arkhe.security.exorcism_cache import ExorcismCache
from src.arkhe.security.domain_profiles import DomainProfile, DomainProfileDetector
from src.arkhe.security.temporal_audit import TemporalAuditLogger
from arkp_core.temporal_chain import TemporalChain
from arkp_security.guardian_attractor import GuardianAttractor
from tests.red_team.adversarial_prompts import RedTeamDataset

class Substrato172Omega:
    """
    Entronização do Guardião Atratora v2 como Substrato 172.
    """
    def __init__(self):
        self.temporal_chain = TemporalChain()
        self.domain_detector = DomainProfileDetector()

        # O Guardião Atratora integra os componentes
        self.guardian = GuardianAttractor(
            vocab_size=500,
            embed_dim=64,
            temperature=0.8,
            exorcist_severity_threshold=0.70,
            attractor_alpha=1.0,
            temporal_chain=self.temporal_chain
        )

        # Adicionar as novas capacidades
        self.guardian.exorcism_cache = ExorcismCache()
        self.guardian.audit_logger = TemporalAuditLogger(self.temporal_chain) if self.temporal_chain else None
        self.guardian.domain = DomainProfile.DEFAULT

    def set_domain(self, domain_name: str):
        try:
            domain = DomainProfile(domain_name)
            self.guardian.domain = domain
            profile = self.domain_detector.get_profile(domain)
            print(f"Domain set to {domain_name}. Profile description: {profile.description}")
        except ValueError:
            print(f"Invalid domain: {domain_name}")

if __name__ == "__main__":
    print("Inicializando Substrato 172-OMEGA (O Guardião Atratora v2)...")
    substrato = Substrato172Omega()
    print("Componentes integrados com sucesso:")
    print("- Exorcism Cache")
    print("- Domain Profiles")
    print("- Temporal Audit Logger")
    print("- Red Team Validation Dataset available")
