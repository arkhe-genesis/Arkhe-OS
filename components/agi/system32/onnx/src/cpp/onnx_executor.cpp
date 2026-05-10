#include "hardware_providers.h"
#include <onnxruntime_cxx_api.h>
#include <iostream>
#include <vector>
#include <string>
#include <memory>

namespace arkhe::onnx {
    class NativeExecutor {
    public:
        explicit NativeExecutor(const std::string& model_path,
                                const std::vector<std::string>& providers = {"CPUExecutionProvider"}) {
            Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "ARKHE_ONNX");
            Ort::SessionOptions session_options;

            for (const auto& provider : providers) {
                session_options.AppendExecutionProvider(provider);
            }
            session_ = std::make_unique<Ort::Session>(env, model_path.c_str(), session_options);
        }

        std::vector<std::vector<float>> Run(const std::vector<float>& inputs,
                                            const std::vector<int64_t>& input_shape) {
            auto input_names = GetInputNames();
            auto output_names = GetOutputNames();

            std::vector<Ort::Value> input_tensors;
            input_tensors.push_back(Ort::Value::CreateTensor<float>(
                Ort::MemoryInfo::CreateCpu(OrtDeviceAllocator, OrtMemTypeCPU),
                const_cast<float*>(inputs.data()), inputs.size(),
                input_shape.data(), input_shape.size()
            ));

            auto output_tensors = session_->Run(Ort::RunOptions{nullptr},
                                                input_names.data(), input_tensors.data(), 1,
                                                output_names.data(), 1);

            std::vector<std::vector<float>> results;
            for (size_t i = 0; i < output_names.size(); ++i) {
                auto* tensor_ptr = output_tensors[i].GetTensorMutableData<float>();
                auto shape = output_tensors[i].GetTensorTypeAndShapeInfo().GetShape();
                size_t size = 1;
                for (auto dim : shape) size *= dim;
                results.emplace_back(tensor_ptr, tensor_ptr + size);
            }
            return results;
        }

    private:
        std::unique_ptr<Ort::Session> session_;
        std::vector<std::string> GetInputNames() {
            std::vector<std::string> names;
            for(size_t i=0; i<session_->GetInputCount(); ++i)
                names.push_back(session_->GetInputNameAllocated(i, Ort::AllocatorWithDefaultOptions()).get());
            return names;
        }
        std::vector<std::string> GetOutputNames() {
            std::vector<std::string> names;
            for(size_t i=0; i<session_->GetOutputCount(); ++i)
                names.push_back(session_->GetOutputNameAllocated(i, Ort::AllocatorWithDefaultOptions()).get());
            return names;
        }
    };
}
