#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugin_sdk.py — SDK para Desenvolvimento de Plugins Éticos
Fornece classes base, decoradores e utilitários de teste para criadores.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class EthicalPlugin(ABC):
    """Classe base para plugins éticos no marketplace ARKHE."""

    @property
    @abstractmethod
    def plugin_metadata(self) -> Dict[str, Any]:
        """Retorna metadados do plugin (id, nome, domínio, versão)."""
        pass

    @abstractmethod
    def evaluate(self, package_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia um pacote de acordo com as regras do plugin.
        Retorna dicionário com: score (0.0 a 1.0), violações, recomendações.
        """
        pass

def arkhe_plugin(metadata: Dict[str, Any]):
    """Decorador para simplificar a criação de plugins."""
    def decorator(cls):
        class WrappedPlugin(cls, EthicalPlugin):
            @property
            def plugin_metadata(self):
                return metadata
        return WrappedPlugin
    return decorator

class PluginTester:
    """Utilitário para testar plugins localmente antes da submissão."""

    @staticmethod
    def run_tests(plugin: EthicalPlugin, test_cases: List[Dict]) -> bool:
        """Executa casos de teste e verifica saídas esperadas."""
        passed = True
        for i, case in enumerate(test_cases):
            result = plugin.evaluate(case['input'], case.get('context', {}))
            if result.get('score') != case['expected_score']:
                print(f"Test {i} failed: Expected {case['expected_score']}, got {result.get('score')}")
                passed = False
        return passed
