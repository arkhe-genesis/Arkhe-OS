#!/usr/bin/env python3
"""
Launcher test for Substrato 9012 - Arkhe-IPython
"""
import sys
import os

# Add local path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'substrates/9012_arkhe_ipython/arkhe-ipython/src')))

try:
    import arkhe_ipython
    from arkhe_ipython.utils import SafeCoreConnection
    from arkhe_ipython.kernel import ArkheKernel
    print(f"✅ Arkhe-IPython (Substrato 9012) loaded successfully!")
    print(f"Version: {arkhe_ipython.__version__}")
except ImportError as e:
    print(f"❌ Failed to load Arkhe-IPython: {e}")
    sys.exit(1)
