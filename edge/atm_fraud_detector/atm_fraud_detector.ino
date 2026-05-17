/*
  Substrato 200: ATM Fraud Detector (Edge)
  TinyML inference on ESP32 for ATM terminals.
*/

#include <Arduino.h>
// #include <TensorFlowLite_ESP32.h>
// Simulated inclusion of TFLite Micro

const int SENSOR_PIN = 34; // Simulating magnetic stripe or chip reading timing sensor

void setup() {
  Serial.begin(115200);
  Serial.println("Arkhe OS: ATM Fraud Detector Initialized.");
  Serial.println("Loading TFLite Micro Anomaly Detection Model...");
  // Simulated Model Load
  delay(1000);
  Serial.println("Model Loaded. Awaiting transactions.");
}

void loop() {
  // Simulate reading ATM metrics (timing, mechanical vibrations, power draw)
  int sensorValue = analogRead(SENSOR_PIN);

  if (sensorValue > 100) {
     // Perform inference (Mock)
     Serial.print("Transaction detected. Sensor Value: ");
     Serial.println(sensorValue);

     float anomaly_score = (float)random(0, 100) / 100.0;

     if (anomaly_score > 0.85) {
         Serial.println("ALERT: High probability of skimming or physical tampering. Score: " + String(anomaly_score));
         // Send alert to UIM / Sentinel Fabric
     } else {
         Serial.println("Transaction normal. Score: " + String(anomaly_score));
     }

     delay(5000); // Wait before next read
  }

  delay(100);
}
