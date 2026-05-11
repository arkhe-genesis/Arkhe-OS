from setuptools import setup, find_packages

setup(
    name="arkhen-sdk",
    version="1.0.0",
    description="Python SDK for Arkhe(n) Hybrid Architecture (ℂ × ℤ → ℝ⁴)",
    author="Hyperspace AI",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
    ],
    python_requires=">=3.8",
)
