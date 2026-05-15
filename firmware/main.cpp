// firmware/main.cpp
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "model_data.cc"  // anomaly_model_tflite
#include "secrets.h"      // Contains SSID and PASSWORD definitions

constexpr int kTensorArenaSize = 8 * 1024;
uint8_t tensor_arena[kTensorArenaSize];

// Wi‑Fi + Q‑Bus endpoint
const char* qbus_endpoint = "http://qbus-sidecar.arkhe-staging:8088/tiny/upload";

static tflite::MicroInterpreter* interpreter = nullptr;
static TfLiteTensor* input = nullptr;
static TfLiteTensor* output = nullptr;

void setup() {
    Serial.begin(115200);
    // Conectar Wi‑Fi usando secrets.h
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) { delay(500); }

    // Inicializar TFLite
    static tflite::MicroMutableOpResolver<4> resolver;
    resolver.AddFullyConnected();
    resolver.AddSoftmax();
    static tflite::MicroInterpreter static_interpreter(
        tflite::GetModel(anomaly_model_tflite), resolver, tensor_arena, kTensorArenaSize);
    interpreter = &static_interpreter;
    interpreter->AllocateTensors();
    input = interpreter->input(0);
    output = interpreter->output(0);
}

void loop() {
    // Ler sensor de vibração (simulado ou via ADXL345)
    float sensor_data[64];
    // Preencher com dados reais do ADXL345 (I2C) ou simulado
    for (int i = 0; i < 64; i++) sensor_data[i] = analogRead(34) / 4095.0;

    // Quantizar entrada para int8
    for (int i = 0; i < 64; i++) input->data.int8[i] = sensor_data[i] * 127;

    interpreter->Invoke();

    // Probabilidade de anomalia (softmax output)
    float anomaly_prob = (output->data.int8[1] - 128) / 127.0; // exemplo simples

    if (anomaly_prob > 0.8) {
        // Enviar alerta via Q‑Bus (HTTP POST)
        HTTPClient http;
        http.begin(qbus_endpoint);
        http.addHeader("Content-Type", "application/json");
        String payload = "{\"node\":\"esp32-s3-01\",\"anomaly\":" + String(anomaly_prob) + ",\"phi_c\":0.997}";
        http.POST(payload);
        http.end();
    }

    delay(1000);
}
