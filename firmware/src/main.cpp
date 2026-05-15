// firmware/src/main.cpp
// Substrato 192: Agente TinyML para ESP32-S3 com detecção de anomalias

#include <Arduino.h>
#include <Wire.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "anomaly_model.h"  // Modelo TFLite convertido para array C++
#include "scaler_params.h"  // Parâmetros do StandardScaler

// Configurações do sensor ADXL345
#define ADXL345_ADDR 0x53
#define SAMPLE_RATE_HZ 100
#define WINDOW_SIZE 64

// Buffer de inferência
float input_buffer[7];  // [acc_x, acc_y, acc_z, freq_dom, rms, kurt, skew]
int8_t quantized_input[7];
int8_t output_buffer[2];

// Runtime TFLite Micro
tflite::MicroErrorReporter micro_error_reporter;
tflite::ErrorReporter* error_reporter = &micro_error_reporter;
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;
constexpr int kTensorArenaSize = 8 * 1024;
uint8_t tensor_arena[kTensorArenaSize];

// Estado do agente
bool anomaly_detected = false;
uint32_t last_inference_ms = 0;
const uint32_t INFERENCE_INTERVAL_MS = 1000;  // Inferir a cada 1 segundo

void init_adxl345();
void collect_vibration_window(float* buffer, int size);
void extract_features(float* window, int size, float* features);
void apply_scaler(float* features, int n);
void trigger_local_action();
void send_to_qbus(bool anomaly, float confidence);

void setup() {
    Serial.begin(115200);
    Wire.begin();

    // Inicializar ADXL345
    init_adxl345();

    // Carregar modelo TFLite
    model = tflite::GetModel(anomaly_model_tflite);
    if (model->version() != TFLITE_SCHEMA_VERSION) {
        error_reporter->Report("Model version mismatch");
        while (1);
    }

    // Registrar operadores
    static tflite::MicroMutableOpResolver<4> resolver;
    resolver.AddFullyConnected();
    resolver.AddSoftmax();
    resolver.AddDequantize();
    resolver.AddQuantize();

    // Criar interpreter
    static tflite::MicroInterpreter static_interpreter(
        model, resolver, tensor_arena, kTensorArenaSize, error_reporter);
    interpreter = &static_interpreter;

    // Alocar tensores
    TfLiteStatus allocate_status = interpreter->AllocateTensors();
    if (allocate_status != kTfLiteOk) {
        error_reporter->Report("Tensor allocation failed");
        while (1);
    }

    // Obter tensores de entrada/saída
    input = interpreter->input(0);
    output = interpreter->output(0);

    Serial.println("✅ ARKHE TinyML Agent initialized");
}

void loop() {
    // Coletar janela de vibração
    if (millis() - last_inference_ms >= INFERENCE_INTERVAL_MS) {
        float window[WINDOW_SIZE * 3];  // XYZ acelerômetros
        collect_vibration_window(window, WINDOW_SIZE);

        // Extrair features
        extract_features(window, WINDOW_SIZE, input_buffer);

        // Aplicar scaler (normalização edge)
        apply_scaler(input_buffer, 7);

        // Quantizar para int8 (TFLite Micro)
        for (int i = 0; i < 7; i++) {
            quantized_input[i] = static_cast<int8_t>(
                input_buffer[i] * 128.0f);  // Simple quantization
        }

        // Copiar para tensor de entrada
        for (int i = 0; i < 7; i++) {
            input->data.int8[i] = quantized_input[i];
        }

        // Executar inferência
        TfLiteStatus invoke_status = interpreter->Invoke();
        if (invoke_status != kTfLiteOk) {
            error_reporter->Report("Inference failed");
            return;
        }

        // Interpretar saída
        float normal_prob = output->data.int8[0] / 128.0f;
        float anomaly_prob = output->data.int8[1] / 128.0f;

        anomaly_detected = (anomaly_prob > 0.95f);

        // Ação local se anomalia detectada
        if (anomaly_detected) {
            Serial.println("🚨 ANOMALY DETECTED — Local action triggered");
            trigger_local_action();  // Ex: desligar motor, alertar via Q-Bus
        }

        // Enviar métricas para Q-Bus se disponível
        send_to_qbus(anomaly_detected, anomaly_prob);

        last_inference_ms = millis();
    }

    delay(10);  // Manter loop responsivo
}

// Funções auxiliares (implementações simplificadas)
void init_adxl345() {
    Wire.beginTransmission(ADXL345_ADDR);
    Wire.write(0x2D);  // POWER_CTL register
    Wire.write(0x08);  // Enable measurement
    Wire.endTransmission();
}

void collect_vibration_window(float* buffer, int size) {
    for (int i = 0; i < size; i++) {
        // Ler ADXL345 (simplificado)
        Wire.beginTransmission(ADXL345_ADDR);
        Wire.write(0x32);  // DATAX0 register
        Wire.endTransmission();
        Wire.requestFrom(ADXL345_ADDR, 6);

        int16_t x = Wire.read() | (Wire.read() << 8);
        int16_t y = Wire.read() | (Wire.read() << 8);
        int16_t z = Wire.read() | (Wire.read() << 8);

        buffer[i*3 + 0] = x * 0.0039f;  // Convert to g
        buffer[i*3 + 1] = y * 0.0039f;
        buffer[i*3 + 2] = z * 0.0039f;

        delayMicroseconds(10000);  // 100 Hz sample rate
    }
}

void extract_features(float* window, int size, float* features) {
    // Calcular RMS, frequência dominante, kurtosis, skewness (simplificado)
    float sum_sq = 0;
    for (int i = 0; i < size * 3; i++) {
        sum_sq += window[i] * window[i];
    }
    features[4] = sqrt(sum_sq / (size * 3));  // RMS

    // Features adicionais seriam calculadas aqui...
    features[0] = 0.0;  // acc_x mean
    features[1] = 0.0;  // acc_y mean
    features[2] = 0.0;  // acc_z mean
    features[3] = 50.0; // freq_dominant (exemplo)
    features[5] = 0.0;  // kurtosis
    features[6] = 0.0;  // skewness
}

void apply_scaler(float* features, int n) {
    // Aplicar parâmetros do StandardScaler (mean, std) salvos no firmware
    // Mock for now
    for (int i = 0; i < n; i++) {
        features[i] = features[i];
    }
}

void trigger_local_action() {
    // Ação local segura: ex: acionar relay, enviar alerta via UART
    digitalWrite(LED_BUILTIN, HIGH);
    delay(200);
    digitalWrite(LED_BUILTIN, LOW);
}

void send_to_qbus(bool anomaly, float confidence) {
    // Enviar via UART para módulo Q-Bus (Wi-Fi/BLE)
    Serial.printf("QBUS:{\"anomaly\":%s,\"confidence\":%.3f,\"ts\":%lu}\n",
                  anomaly ? "true" : "false", confidence, millis());
}
