from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

ext_modules = [
    Pybind11Extension(
        "zee200_backend",
        ["zee200_bindings.cpp"],
        include_dirs=[
            "ZEE200/include",
        ],
        cxx_std=17,
    ),
]

setup(
    name="zee200_backend",
    version="0.1.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
