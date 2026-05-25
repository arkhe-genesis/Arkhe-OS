// clg_arduino_control.ino
// Controlador e monitor da Chiral Logic Gate (Substrato 816.3-C)
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-25
// Plataforma: Arduino Uno / Nano / RP2040 (Pico)

// Pinos
const int PIN_CHI     = 2;   // Controle de quiralidade (HIGH=R, LOW=L)
const int PIN_INPUT   = 3;   // Input digital (0 ou 1)
const int PIN_OUTPUT  = 4;   // Output do escravo (leitura)
const int PIN_XOR_ADC = A0;  // Saída do XOR (medida de Δθ via ADC)
const int PIN_LED_R   = 5;   // LED modo R
const int PIN_LED_L   = 6;   // LED modo L
const int PIN_SYNC    = 7;   // LED sincronização detectada

// Parâmetros
const int SAMPLE_WINDOW = 50;      // amostras para média
const int SYNC_THRESHOLD = 100;    // valor ADC para detectar sincronia
const unsigned long SETTLE_MS = 2000; // tempo de estabilização após switch

void setup() {
  Serial.begin(115200);
  pinMode(PIN_CHI, OUTPUT);
  pinMode(PIN_INPUT, OUTPUT);
  pinMode(PIN_OUTPUT, INPUT);
  pinMode(PIN_LED_R, OUTPUT);
  pinMode(PIN_LED_L, OUTPUT);
  pinMode(PIN_SYNC, OUTPUT);

  Serial.println(F("========================================"));
  Serial.println(F("CLG-816 Chiral Logic Gate Controller"));
  Serial.println(F("Substrato 816-CHIRALITY-IMPLEMENTATION"));
  Serial.println(F("========================================"));
  Serial.println(F("Comandos: R | L | 0 | 1 | TEST | STATUS"));
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();
    processCommand(cmd);
  }
}

void processCommand(String cmd) {
  if (cmd == "R") {
    setChirality(true);
    Serial.println(F("[CMD] Modo R (IDENTITY) — α > 0"));
  }
  else if (cmd == "L") {
    setChirality(false);
    Serial.println(F("[CMD] Modo L (NOT) — α < 0"));
  }
  else if (cmd == "0") {
    setInput(false);
    Serial.println(F("[CMD] Input = 0 (fase 0)"));
  }
  else if (cmd == "1") {
    setInput(true);
    Serial.println(F("[CMD] Input = 1 (fase π)"));
  }
  else if (cmd == "TEST") {
    runFullTest();
  }
  else if (cmd == "STATUS") {
    printStatus();
  }
  else {
    Serial.println(F("[ERR] Comando desconhecido. Use: R | L | 0 | 1 | TEST | STATUS"));
  }
}

void setChirality(bool right) {
  digitalWrite(PIN_CHI, right ? HIGH : LOW);
  digitalWrite(PIN_LED_R, right ? HIGH : LOW);
  digitalWrite(PIN_LED_L, right ? LOW : HIGH);
  delay(SETTLE_MS); // aguardar sincronização
}

void setInput(bool high) {
  digitalWrite(PIN_INPUT, high ? HIGH : LOW);
  delay(100); // tempo de propagação
}

bool readOutput() {
  return digitalRead(PIN_OUTPUT) == HIGH;
}

int readPhaseDifference() {
  long sum = 0;
  for (int i = 0; i < SAMPLE_WINDOW; i++) {
    sum += analogRead(PIN_XOR_ADC);
    delayMicroseconds(100);
  }
  return (int)(sum / SAMPLE_WINDOW);
}

bool isSynchronized() {
  int phaseDiff = readPhaseDifference();
  // XOR output ≈ 0V quando fases iguais, ≈ VCC/2 quando opostas
  // Em 5V com ADC 10-bit: 0V → 0, 2.5V → ~512
  return (phaseDiff < SYNC_THRESHOLD) || (abs(phaseDiff - 512) < SYNC_THRESHOLD);
}

void runFullTest() {
  Serial.println(F("\n--- FULL TEST SEQUENCE ---"));
  bool allPass = true;

  // Teste 1: R + 0 → 0 (IDENTITY)
  setChirality(true);
  setInput(false);
  bool out1 = readOutput();
  bool sync1 = isSynchronized();
  bool pass1 = (out1 == false) && sync1;
  Serial.print(F("TEST R+0: ")); Serial.print(out1); Serial.print(F(" SYNC=")); Serial.print(sync1);
  Serial.println(pass1 ? F(" PASS") : F(" FAIL"));
  allPass &= pass1;

  // Teste 2: R + 1 → 1 (IDENTITY)
  setInput(true);
  bool out2 = readOutput();
  bool sync2 = isSynchronized();
  bool pass2 = (out2 == true) && sync2;
  Serial.print(F("TEST R+1: ")); Serial.print(out2); Serial.print(F(" SYNC=")); Serial.print(sync2);
  Serial.println(pass2 ? F(" PASS") : F(" FAIL"));
  allPass &= pass2;

  // Teste 3: L + 0 → 1 (NOT)
  setChirality(false);
  setInput(false);
  bool out3 = readOutput();
  bool sync3 = isSynchronized();
  bool pass3 = (out3 == true) && sync3;
  Serial.print(F("TEST L+0: ")); Serial.print(out3); Serial.print(F(" SYNC=")); Serial.print(sync3);
  Serial.println(pass3 ? F(" PASS") : F(" FAIL"));
  allPass &= pass3;

  // Teste 4: L + 1 → 0 (NOT)
  setInput(true);
  bool out4 = readOutput();
  bool sync4 = isSynchronized();
  bool pass4 = (out4 == false) && sync4;
  Serial.print(F("TEST L+1: ")); Serial.print(out4); Serial.print(F(" SYNC=")); Serial.print(sync4);
  Serial.println(pass4 ? F(" PASS") : F(" FAIL"));
  allPass &= pass4;

  // Teste 5: Reversibilidade (L→R→L)
  setChirality(true);
  delay(SETTLE_MS);
  bool out5a = readOutput();
  setChirality(false);
  delay(SETTLE_MS);
  bool out5b = readOutput();
  bool pass5 = (out5a != out5b); // deve inverter
  Serial.print(F("TEST REV: ")); Serial.print(out5a); Serial.print(F("→")); Serial.print(out5b);
  Serial.println(pass5 ? F(" PASS") : F(" FAIL"));
  allPass &= pass5;

  Serial.print(F("\n=== RESULTADO: "));
  Serial.println(allPass ? F("ALL PASS — CLG operacional") : F("FAIL — requer calibração"));
  digitalWrite(PIN_SYNC, allPass ? HIGH : LOW);
}

void printStatus() {
  bool chi = digitalRead(PIN_CHI) == HIGH;
  bool inp = digitalRead(PIN_INPUT) == HIGH;
  bool out = readOutput();
  int phase = readPhaseDifference();
  bool sync = isSynchronized();

  Serial.println(F("\n--- STATUS ---"));
  Serial.print(F("CHI (α): ")); Serial.println(chi ? F("R (+)") : F("L (−)"));
  Serial.print(F("INPUT:   ")); Serial.println(inp ? F("1 (π)") : F("0 (0)"));
  Serial.print(F("OUTPUT:  ")); Serial.println(out ? F("1 (π)") : F("0 (0)"));
  Serial.print(F("Δθ ADC:  ")); Serial.println(phase);
  Serial.print(F("SYNC:    ")); Serial.println(sync ? F("YES") : F("NO"));
  Serial.print(F("Operação:"));
  if (chi) {
    Serial.println(F(" IDENTITY"));
  } else {
    Serial.println(F(" NOT"));
  }
}
