#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "zmt.h"

namespace py = pybind11;

py::tuple zero_mode_truncation_wrapper(Eigen::MatrixXcd left_env, Eigen::MatrixXcd right_env, int bond_dim, int kappa = 5) {
    Eigen::MatrixXcd U;
    Eigen::VectorXd lambda;
    Eigen::MatrixXcd V;

    zero_mode_truncation(left_env, right_env, bond_dim, kappa, 1e-12, U, lambda, V);

    return py::make_tuple(U, lambda, V);
}

PYBIND11_MODULE(zmt_native, m) {
    m.doc() = "Zero-Mode Truncation Native C++ Module";
    m.def("zero_mode_truncation", &zero_mode_truncation_wrapper, "Apply Zero-Mode Truncation to a bond",
          py::arg("left_env"), py::arg("right_env"), py::arg("bond_dim"), py::arg("kappa") = 5);
}
