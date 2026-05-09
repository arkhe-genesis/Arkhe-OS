#!/usr/bin/env python3
"""setup.py — Legacy setup for ARKHE OS"""
from setuptools import setup, find_packages

setup(
    name="arkhe-agi-core",
    version="5003.1.0",
    packages=find_packages(where=".", include=["agi*"]),
    package_dir={"": "."},
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "networkx>=3.0",
        "pyyaml>=6.0",
        "cryptography>=41.0.0",
        "pysocks>=1.7.1",
    ],
    entry_points={
        "console_scripts": [
            "agictl=agi.system32.cli.main:main",
            "arkhe=agi.main:main",
        ],
    },
)
