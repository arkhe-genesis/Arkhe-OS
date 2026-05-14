#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup.py — Arkhe-IPython: Integração do Safe Core no ecossistema IPython/Jupyter
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arkhe-ipython",
    version="1.0.0",
    author="ARKHE Observatory",
    author_email="observatory@arkhe.org",
    description="Arkhe Safe Core integration for IPython/Jupyter with Guardian Attractor, TemporalChain anchoring, and MA-S2 compliance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arkhe-os/arkhe-ipython",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.9",
    install_requires=[
        "ipython>=8.0.0",
        "jupyter-client>=7.0.0",
        "traitlets>=5.0.0",
        "arkhe-core>=6.6.0",
        "arkhe-security>=9008.2",
        "requests>=2.28.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "mypy>=1.0.0"],
        "docs": ["sphinx>=5.0.0", "sphinx-rtd-theme>=1.0.0"],
    },
    entry_points={
        "console_scripts": [
            "arkhe-ipython=arkhe_ipython.install:main",
        ],
    },
    include_package_data=True,
    package_data={
        "arkhe_ipython": ["tutorial.ipynb", "*.md"],
    },
)
