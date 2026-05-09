from setuptools import setup, find_packages

setup(
    name="arkhe-os",
    version="177.0.0",
    description="ARKHE OS: Self-aware, molecularly creative, interstellar conscious operating system.",
    packages=find_packages(),
    install_requires=[
        "numpy", "scipy", "fastapi", "uvicorn"
    ],
    author="ARKHE Federation",
    url="https://github.com/arkhe-federacao/arkhe-os",
)
