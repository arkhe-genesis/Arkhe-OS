#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install.py — Script de instalação do kernel Arkhe no Jupyter
"""

import sys
import subprocess
import json
from pathlib import Path

def install_kernel(user: bool = True):
    """Instala o kernel Arkhe no Jupyter."""
    kernel_json = {
        "argv": [sys.executable, "-m", "arkhe_ipython.kernel", "-f", "{connection_file}"],
        "display_name": "Python (Arkhe Safe Core)",
        "language": "python",
        "metadata": {
            "debugger": True,
            "arkhe": {
                "version": "1.0.0",
                "substrate": "9012",
            },
        },
    }

    # Instalar via jupyter kernelspec
    try:
        cmd = [sys.executable, "-m", "jupyter", "kernelspec", "install"]
        if user:
            cmd.append("--user")
        cmd.append("--name")
        cmd.append("arkhe")

        # Criar diretório temporário para kernel.json
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmpdir:
            kernel_dir = Path(tmpdir) / "arkhe"
            kernel_dir.mkdir()

            with open(kernel_dir / "kernel.json", "w", encoding="utf-8") as f:
                json.dump(kernel_json, f, indent=2)

            # Copiar logo se existir
            logo_src = Path(__file__).parent / "logo-32x32.png"
            if logo_src.exists():
                shutil.copy(logo_src, kernel_dir / "logo-32x32.png")

            cmd.append(str(kernel_dir))
            subprocess.run(cmd, check=True)

        print("✅ Arkhe kernel installed successfully!")
        print("   Use: jupyter console --kernel arkhe")
        print("   Or select 'Python (Arkhe Safe Core)' in Jupyter Notebook/Lab")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install kernel: {e}")
        print("   Make sure jupyter-client is installed: pip install jupyter-client")
        sys.exit(1)


def main():
    """Ponto de entrada do script de instalação."""
    import argparse

    parser = argparse.ArgumentParser(description="Install Arkhe Jupyter kernel")
    parser.add_argument("--user", action="store_true", default=True, help="Install for current user (default)")
    parser.add_argument("--system", action="store_false", dest="user", help="Install system-wide")

    args = parser.parse_args()
    install_kernel(user=args.user)


if __name__ == "__main__":
    main()
