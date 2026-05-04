// arkhe_esp32_sensor.ino
// Firmware base para Nó Sensorial do Casulo com Suporte a Tamper, Modo Zumbi e Detecção de Fratura
// Compatível com ESP32, ESP32-C3, ESP32-C6, ESP32-S3
// Autoria: O Ferreiro
// Odômetro: 001445

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <esp_sleep.h>
#include <driver/rtc_io.h>
#include <Preferences.h>
#include <arduinoFFT.h>
#include <driver/i2s.h>

// ============= DEFINIÇÕES DE PINOS =============
#define TAMPER_PIN      4    // GPIO4 — reed switch ou fio de malha
#define LED_PIN         2    // LED onboard para sinalização
#define I2S_WS          16
#define I2S_SD          14
#define I2S_SCK         17
#define I2S_PORT        I2S_NUM_0

// ============= CONFIGURAÇÕES =============
const char* WIFI_SSID = "ArkheNet";
const char* WIFI_PASS = "quartz_silence";
const char* ARKHE_ENDPOINT = "https://api.arkhe.ai/quartz/v1/telemetry";
const char* DEVICE_JWT_DEFAULT = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9..."; // Mock JWT base

// Hesitação: thresholds de transmissão
const float TEMP_HESITATION_THRESHOLD = 0.5;   // °C
const float HUMIDITY_HESITATION_THRESHOLD = 2.0; // %
const int HESITATION_INTERVAL_SEC = 300;        // 5 minutos entre verificações ULP

// FFT para Fratura de Quartzo
#define SAMPLES         512
#define SAMPLING_FREQ   16000
#define FRACTURE_THRESHOLD 100.0

// Declarations first
double vReal[SAMPLES];
double vImag[SAMPLES];

// arduinoFFT instantiation - compatibility with v1.x and v2.x
#ifdef ARDUINO_FFT_VERSION
  arduinoFFT FFT = arduinoFFT(vReal, vImag, SAMPLES, SAMPLING_FREQ);
#else
  arduinoFFT FFT = arduinoFFT();
#endif

// ============= VARIÁVEIS RTC (persistem em deep sleep) =============
RTC_DATA_ATTR float last_transmitted_temp = 0.0;
RTC_DATA_ATTR float last_transmitted_humidity = 0.0;
RTC_DATA_ATTR int boot_count = 0;
RTC_DATA_ATTR bool tamper_flag = false;
RTC_DATA_ATTR int tamper_boot_count = 0;

// ============= SETUP =============
void setup() {
    Serial.begin(115200);
    boot_count++;

    // Configura pino de tamper como wake-up source
    esp_sleep_enable_ext0_wakeup((gpio_num_t)TAMPER_PIN, 0); // LOW = violação

    // Recupera razão do wake-up
    esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();

    // ============= MODO ZUMBI =============
    if (tamper_flag) {
        zombie_mode();
        return;
    }

    // ============= DETECÇÃO DE TAMPER =============
    if (wakeup_reason == ESP_SLEEP_WAKEUP_EXT0) {
        handle_tamper_event();
        return;
    }

    // ============= INICIALIZAÇÃO I2S =============
    setup_i2s();

    // ============= OPERAÇÃO NORMAL =============
    // 1. Escuta por Fraturas (Ritual de Passagem)
    if (detect_quartz_fracture()) {
        connect_wifi();
        send_fracture_event(4250.0, -12.5, 187); // Valores exemplo do Anexo AK
    }

    // 2. Telemetria Ambiental
    float temp = read_temperature();
    float hum = read_humidity();

    if (should_transmit(temp, hum)) {
        connect_wifi();
        send_telemetry(temp, hum);
        last_transmitted_temp = temp;
        last_transmitted_humidity = hum;
    }

    // Configura wake-up por timer para o próximo ciclo de hesitação
    esp_sleep_enable_timer_wakeup(HESITATION_INTERVAL_SEC * 1000000ULL);
    Serial.println("[ARKHE] Hesitando...");
    esp_deep_sleep_start();
}

// ============= I2S SETUP =============
void setup_i2s() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLING_FREQ,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 64,
        .use_apll = false
    };
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD
    };
    i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_PORT, &pin_config);
}

// ============= UUID GENERATOR =============
String generate_event_id() {
    char uuid[37];
    uint32_t r1 = esp_random();
    uint32_t r2 = esp_random();
    uint32_t r3 = esp_random();
    uint32_t r4 = esp_random();
    sprintf(uuid, "%08x-%04x-%04x-%04x-%04x%08x",
            r1,
            (uint16_t)(r2 >> 16),
            (uint16_t)(r2 & 0x0fff) | 0x4000,
            (uint16_t)(r3 >> 16) | 0x8000,
            (uint16_t)(r3 & 0xffff),
            r4);
    return String(uuid);
}

// ============= DETECÇÃO DE FRATURA FFT =============
bool detect_quartz_fracture() {
    size_t bytes_read;
    int32_t samples_buffer[SAMPLES];
    i2s_read(I2S_PORT, &samples_buffer, sizeof(samples_buffer), &bytes_read, portMAX_DELAY);

    for(int i=0; i<SAMPLES; i++) {
        vReal[i] = (double)samples_buffer[i];
        vImag[i] = 0;
    }

    #ifdef ARDUINO_FFT_VERSION
      FFT.windowing(FFT_WIN_TYP_HAMMING, FFT_FORWARD);
      FFT.compute(FFT_FORWARD);
      FFT.complexToMagnitude();
      double peak = FFT.majorPeak();
    #else
      FFT.Windowing(vReal, SAMPLES, FFT_WIN_TYP_HAMMING, FFT_FORWARD);
      FFT.Compute(vReal, vImag, SAMPLES, FFT_FORWARD);
      FFT.ComplexToMagnitude(vReal, vImag, SAMPLES);
      double peak = FFT.MajorPeak(vReal, SAMPLES, SAMPLING_FREQ);
    #endif

    return (peak > 2000 && peak < 8000);
}

// ============= HANDLER DE TAMPER =============
void handle_tamper_event() {
    Serial.println("🚨 TAMPER DETECTADO!");
    Preferences prefs;
    prefs.begin("arkhe", false);
    prefs.clear();
    prefs.end();
    tamper_flag = true;
    ESP.restart();
}

// ============= MODO ZUMBI =============
void zombie_mode() {
    tamper_boot_count++;
    pinMode(LED_PIN, OUTPUT);

    // Padrão SOS (um único ciclo para economizar bateria)
    for(int i=0; i<3; i++) { digitalWrite(LED_PIN, HIGH); delay(200); digitalWrite(LED_PIN, LOW); delay(200); }
    delay(500);
    for(int i=0; i<3; i++) { digitalWrite(LED_PIN, HIGH); delay(600); digitalWrite(LED_PIN, LOW); delay(200); }
    delay(500);
    for(int i=0; i<3; i++) { digitalWrite(LED_PIN, HIGH); delay(200); digitalWrite(LED_PIN, LOW); delay(200); }

    Serial.printf("MODO ZUMBI ATIVO. Boot #%d.\n", tamper_boot_count);

    // Dormir por 24 horas para silêncio e resiliência
    esp_sleep_enable_timer_wakeup(24 * 60 * 60 * 1000000ULL);
    esp_deep_sleep_start();
}

// ============= SENSORES (STUBS PARA DHT22/BME280) =============
float read_temperature() {
    // TODO: Implementar leitura real de sensor I2C/OneWire
    return 24.5 + (random(-10, 10) / 10.0);
}

float read_humidity() {
    return 50.0 + (random(-20, 20) / 10.0);
}

bool should_transmit(float temp, float hum) {
    return (abs(temp - last_transmitted_temp) > TEMP_HESITATION_THRESHOLD) ||
           (abs(hum - last_transmitted_humidity) > HUMIDITY_HESITATION_THRESHOLD);
}

// ============= COMUNICAÇÃO =============
void connect_wifi() {
    if (WiFi.status() == WL_CONNECTED) return;
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 15) { delay(500); retries++; }
}

String get_jwt() {
    Preferences prefs;
    prefs.begin("arkhe", true);
    String jwt = prefs.getString("jwt", DEVICE_JWT_DEFAULT);
    prefs.end();
    return jwt;
}

void send_telemetry(float temp, float hum) {
    if (WiFi.status() != WL_CONNECTED) return;
    HTTPClient https;
    https.begin(ARKHE_ENDPOINT);
    https.addHeader("Content-Type", "application/json");
    https.addHeader("Authorization", "Bearer " + get_jwt());

    StaticJsonDocument<512> doc;
    doc["event_id"] = generate_event_id();
    doc["action_type"] = "sensor_reading";
    doc["target"]["entity_type"] = "environmental_sensor";
    doc["target"]["entity_id"] = "esp32_palmetto_01";
    doc["metadata"]["temperature_c"] = temp;
    doc["metadata"]["humidity_pct"] = hum;

    String payload;
    serializeJson(doc, payload);
    https.POST(payload);
    https.end();
}

void send_fracture_event(float freq, float energy, int duration) {
    if (WiFi.status() != WL_CONNECTED) return;
    HTTPClient https;
    https.begin(ARKHE_ENDPOINT);
    https.addHeader("Content-Type", "application/json");
    https.addHeader("Authorization", "Bearer " + get_jwt());

    StaticJsonDocument<512> doc;
    doc["event_id"] = generate_event_id();
    doc["action_type"] = "fracture_detected";
    doc["target"]["entity_type"] = "quartz_crystal";
    doc["target"]["entity_id"] = "crystal_palmetto_01";
    doc["metadata"]["peak_frequency_hz"] = freq;
    doc["metadata"]["peak_energy_db"] = energy;
    doc["metadata"]["fracture_duration_ms"] = duration;

    String payload;
    serializeJson(doc, payload);
    https.POST(payload);
    https.end();
}

void loop() {}
