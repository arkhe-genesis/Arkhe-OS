#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "arkhe_edge_runtime.h"

namespace py = pybind11;

PYBIND11_MODULE(arkhe_edge_runtime_module, m) {
    m.doc() = "Arkhe Edge AI Runtime — LiteRT C++ inference with Φ_C anchoring";

    py::enum_<HwBackend>(m, "HwBackend")
        .value("AUTO", HwBackend::kAuto)
        .value("ARM_SME2", HwBackend::kArmSME2)
        .value("QUALCOMM_HEXAGON", HwBackend::kQualcommHexagon)
        .value("APPLE_ANE", HwBackend::kAppleANE)
        .value("INTEL_NPU", HwBackend::kIntelNPU)
        .value("AMD_XDNA2", HwBackend::kAMDXDNA2)
        .value("FALLBACK_CPU", HwBackend::kFallbackCPU)
        .export_values();

    py::class_<InferenceConfig>(m, "InferenceConfig")
        .def(py::init<>())
        .def_readwrite("model_path", &InferenceConfig::model_path)
        .def_readwrite("preferred_backend", &InferenceConfig::preferred_backend)
        .def_readwrite("num_threads", &InferenceConfig::num_threads)
        .def_readwrite("enable_temporal_anchor", &InferenceConfig::enable_temporal_anchor)
        .def_readwrite("enable_phi_c_validation", &InferenceConfig::enable_phi_c_validation)
        .def_readwrite("phi_c_threshold", &InferenceConfig::phi_c_threshold);

    py::class_<InferenceResult>(m, "InferenceResult")
        .def_readonly("success", &InferenceResult::success)
        .def_readonly("latency_ms", &InferenceResult::latency_ms)
        .def_readonly("phi_c_before", &InferenceResult::phi_c_before)
        .def_readonly("phi_c_after", &InferenceResult::phi_c_after)
        .def_readonly("temporal_seal", &InferenceResult::temporal_seal)
        .def_readonly("backend_used", &InferenceResult::backend_used)
        .def_readonly("output_data", &InferenceResult::output_data);

    py::class_<ArkheEdgeRuntime>(m, "ArkheEdgeRuntime")
        .def(py::init<const InferenceConfig&>())
        .def("run", &ArkheEdgeRuntime::Run)
        .def_static("backend_name", &ArkheEdgeRuntime::BackendName);
}
