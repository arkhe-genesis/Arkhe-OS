// firmware/esp32/arkhe_inference.c
#include <stdio.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_log.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

// Buffer de arena para alocação de tensores
constexpr int kTensorArenaSize = 200 * 1024; // 200 KB para ESP32-S3
uint8_t tensor_arena[kTensorArenaSize];

// Modelo ONNX convertido para TFLite (via onnx2tf)
extern const unsigned char g_arkhe_sae_int8_tflite[];
extern const int g_arkhe_sae_int8_tflite_len;

// Ponteiros para tensores de entrada/saída
TfLiteTensor* input_tensor = nullptr;
TfLiteTensor* output_tensor = nullptr;

// Inicializar interpreter
TfLiteStatus InitArkheInterpreter(tflite::MicroInterpreter** interpreter_out) {
  // Carregar modelo
  const tflite::Model* model = tflite::GetModel(g_arkhe_sae_int8_tflite);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    MicroPrintf("Model version mismatch");
    return kTfLiteError;
  }

  // Resolver operadores (apenas os necessários para SAE)
  tflite::AllOpsResolver resolver;

  // Criar interpreter
  static tflite::MicroInterpreter static_interpreter(
      model, resolver, tensor_arena, kTensorArenaSize);
  *interpreter_out = &static_interpreter;

  // Alocar tensores
  TfLiteStatus allocate_status = (*interpreter_out)->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    MicroPrintf("AllocateTensors() failed");
    return allocate_status;
  }

  // Obter tensores de entrada/saída
  input_tensor = (*interpreter_out)->input(0);   // [1, 768] float32
  output_tensor = (*interpreter_out)->output(0); // [1, 768] float32

  return kTfLiteOk;
}

// Executar inferência com fases do sensor
float RunCrystalBrainInference(float* phases_input, int batch_size) {
  // Copiar dados de entrada para o tensor
  for (int i = 0; i < batch_size * 768; i++) {
    input_tensor->data.f[i] = phases_input[i];
  }

  // Executar inferência
  TfLiteStatus invoke_status = interpreter->Invoke();
  if (invoke_status != kTfLiteOk) {
    MicroPrintf("Invoke() failed");
    return -1.0f;
  }

  // Extrair código latente e calcular coerência
  float* latent_code = output_tensor->data.f;
  float coherence = ComputeKuramotoOrder(latent_code, batch_size * 768);

  return coherence;
}

// Calcular parâmetro de ordem de Kuramoto (coerência)
float ComputeKuramotoOrder(float* phases, int n) {
  float sum_re = 0.0f, sum_im = 0.0f;
  for (int i = 0; i < n; i++) {
    sum_re += cosf(phases[i]);
    sum_im += sinf(phases[i]);
  }
  return sqrtf(sum_re * sum_re + sum_im * sum_im) / n;
}

// Loop principal do firmware
void setup() {
  Serial.begin(115200);

  tflite::MicroInterpreter* interpreter = nullptr;
  if (InitArkheInterpreter(&interpreter) != kTfLiteOk) {
    Serial.println("❌ Failed to initialize ARKHE interpreter");
    return;
  }
  Serial.println("✅ ARKHE interpreter initialized");
}

void loop() {
  // Ler fases do sensor (exemplo: 768 osciladores via ADC/I2C)
  float phases[768];
  ReadPhasesFromSensors(phases, 768);

  // Executar inferência
  float coherence = RunCrystalBrainInference(phases, 1);

  // Transmitir resultado via BLE/LoRa
  if (coherence > 0.8f) {
    Serial.printf("🟢 CAPTURE regime: ρ = %.3f\n", coherence);
    TransmitCoherenceAlert(coherence);
  } else {
    Serial.printf("🟡 Monitoring: ρ = %.3f\n", coherence);
  }

  delay(1000); // 1 Hz sampling
}
