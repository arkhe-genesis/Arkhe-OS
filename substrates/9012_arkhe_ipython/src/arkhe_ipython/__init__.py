#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_ipython — Substrato 9012: Integração do Safe Core Arkhe no IPython/Jupyter

Este pacote fornece:
• Extensão IPython com magics %arkhe e %%arkhe
• Kernel Jupyter dedicado (ArkheKernel) com proteção do Safe Core
• Ancoragem temporal de cada execução na TemporalChain
• Tutorial interativo para aprendizado progressivo

Versão: 1.0.0
Substrato: 9012
"""

__version__ = "1.0.0"
__substrate__ = "9012"
__author__ = "ARKHE Observatory"
__email__ = "observatory@arkhe.org"

from .magics import load_ipython_extension, unload_ipython_extension
from .kernel import ArkheKernel
from .utils import SafeCoreConnection

__all__ = [
    "load_ipython_extension",
    "unload_ipython_extension",
    "ArkheKernel",
    "SafeCoreConnection",
]

def _jupyter_labextension_paths():
    """Retorna caminhos para extensão JupyterLab (se aplicável)."""
    return []

def _jupyter_nbextension_paths():
    """Retorna caminhos para extensão Jupyter Notebook (se aplicável)."""
    return []
