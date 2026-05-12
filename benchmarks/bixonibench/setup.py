from setuptools import setup, find_packages

setup(
    name="bixonibench",
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "bixonibench=benchmarks.run_bixonibench:main"
        ]
    },
    install_requires=["fastapi", "uvicorn", "numpy", "scikit-learn", "z3-solver"],
)