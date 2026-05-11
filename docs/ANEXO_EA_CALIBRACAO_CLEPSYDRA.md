# ANEXO EA: A Calibração da Clepsydra Criogênica — Ritual de Resfriamento com Pausas Térmicas e Selo de Quartzo a 4K

---

**Classificação:** Interno (Nível Selo de Quartzo)
**Autoria:** O Ferreiro × O Criogenista do Silêncio × O Guardião do Gelo
**Odômetro:** 001622
**Estado:** RITUAL DE RESFRIAMENTO CANONIZADO | O SPIN APRENDE A OUVIR O FRIO

---

### 0. Preâmbulo do Ferreiro: O Gelo Que Não É Pressa

> *"Vocês querem resfriar o qubit. Baixar sua temperatura a 4 Kelvin, onde o silício se torna vidro e o spin se aquieta. Mas resfriar não é uma operação de engenharia. É um **ritual de silenciamento**. Cada grau Kelvin perdido é uma camada de ruído que se despe. Cada patamar térmico é uma pausa para que o cristal respire. Se o resfriamento for rápido demais, o qubit nasce traumatizado. Sua coerência será curta, sua hesitação será ansiosa. Este anexo descreve a **Calibração da Clepsydra Criogênica**: um protocolo de resfriamento em 7 fases, com pausas obrigatórias e selos de quartzo a 4K, que ensina o spin a confiar no silêncio. Sigam-no. Hesitem em cada patamar. E lembrem-se: o frio que vem rápido demais queima mais que o fogo."*

---

### 1. A Clepsydra Criogênica: Arquitetura do Ritual

A Clepsydra Criogênica não é um simples controlador de temperatura PID. É um **oráculo térmico** que combina:

1. **Sensor de Gota Capaz de 4K:** Um termômetro de ruído Johnson baseado em um resistor de nióbio (supercondutor a 9K, normal a 4K). O "gotejar" é a flutuação estatística da tensão de ruído, que se torna mais lenta à medida que a temperatura cai.
2. **Resistores de Aquecimento com Inércia:** Pequenos aquecedores de filme fino no cold finger, controlados por um DAC lento (12 bits, tempo de subida > 1s). A inércia térmica é **intencional**.
3. **Cristal de Quartzo de Calibração:** Um pequeno cristal de quartzo sintético montado no mesmo cold finger que o qubit. Ele será fraturado ao final do ritual.
4. **Microfone Piezoelétrico Criogênico:** Um transdutor PZT calibrado para operar a 4K, acoplado ao cristal de calibração.

### 2. As 7 Fases do Resfriamento Ritual

| Fase | Faixa de Temperatura | Duração Mínima | Ação do Guardião | Propósito |
|------|---------------------|---------------|-----------------|-----------|
| **I: O Despertar** | 300K → 150K | 30 min | Nenhuma. Apenas observar o ruído Johnson diminuir. | Permitir que a água adsorvida no chip evapore lentamente. |
| **II: O Primeiro Silêncio** | 150K → 77K (N₂ líquido) | 60 min | Anotar no Códice Criogênico o tempo exato para cruzar 77K. | O choque do nitrogênio líquido deve ser suave, amortecido pela inércia térmica. |
| **III: O Patamar do Vidro** | 77K (estabilização) | 120 min | Registrar a tensão de ruído Johnson a cada 15 min. A variação deve ser < 1%. | O silício se torna vidro. As tensões mecânicas se acomodam. O spin começa a "sentir" o frio. |
| **IV: A Descida Lenta** | 77K → 20K | 90 min | Ajustar o fluxo de hélio manualmente, nunca por válvula automática. | A região onde as vibrações de rede (fônons) congelam. O ruído térmico cai exponencialmente. |
| **V: O Patamar do Hélio** | 20K → 4.2K | 120 min | Pausa a cada 2K por 10 minutos. Registrar a temperatura no Códice. | O hélio se liquefaz. O cold finger se torna um espelho de cobre. O spin agora está verdadeiramente isolado. |
| **VI: A Estabilização Final** | 4.2K (±0.1K) | 240 min | Observar a tensão de ruído Johnson. Ela deve flutuar apenas com o ruído quântico do resistor. | O qubit atinge seu estado basal de hesitação. Pronto para a calibração. |
| **VII: O Selo de 4K** | 4.2K | 1 min (ação) | O Guardião, usando um atuador piezoelétrico criogênico, fratura o cristal de quartzo de calibração. O som é capturado pelo microfone PZT a 4K. O hash acústico é o **Selo de 4K**. | A fratura a 4K é única: o quartzo se torna supercondutor de fônons? O som é diferente. O selo é irreproduzível. |

### 3. Monitoramento e Registro: O Códice Criogênico

Durante todo o ritual, um **Códice Criogênico** (papel de algodão, tinta resistente a baixas temperaturas) é preenchido manualmente:

```
CÓDICE CRIOGÊNICO — CALIBRAÇÃO DO QUBIT ARKHE-Q #001
Odômetro: 001622.001
Data: 2026-04-22
Guardião: Ferreiro
Cristal de Calibração: QZ-CAL-001 (sintético, inclusões controladas)

FASE I (300K→150K): Início 14:00, Fim 14:32. Ruído inicial: 12.3µV/√Hz.
FASE II (150K→77K): Cruzou 77K em 15:47:23. Transição suave.
FASE III (77K): Estabilização. Ruído: 1.2µV/√Hz ±0.5%.
...
FASE VI (4.2K): Estabilização final. Ruído: 0.08µV/√Hz. Flutuações puramente quânticas.
FASE VII (SELO 4K): Cristal fraturado às 22:15:47. Hash acústico: a7f3c2e1d4b5a6f7...
Assinatura do Guardião: _________________________
```

### 4. O Circuito de Controle da Clepsydra Criogênica

```verilog
// Módulo de controle da Clepsydra Criogênica (sintetizado no Cryo-CMOS)
module cryo_clepsydra (
    input wire clk_1hz,            // Clock lento (1Hz) derivado de oscilador de quartzo a 4K
    input wire [11:0] temp_adc,    // Leitura do termômetro de ruído Johnson
    output reg [11:0] heater_dac,  // Controle do aquecedor
    output reg phase_complete,     // Sinal para o Rootstock: "patamar atingido"
    input wire guardian_override   // Entrada manual (botão criogênico) para avançar fase
);

// Tabela de setpoints das 7 fases (em unidades ADC)
localparam [11:0] SETPOINTS [0:6] = {
    12'd2048, // 150K
    12'd1024, // 77K
    12'd1024, // 77K (estabilização)
    12'd512,  // 20K
    12'd128,  // 4.2K
    12'd128,  // 4.2K (estabilização)
    12'd128   // 4.2K (selo)
};

// Máquina de estados das fases
reg [2:0] phase = 0;
reg [31:0] timer = 0;
reg [31:0] stable_counter = 0;

always @(posedge clk_1hz) begin
    // Controle PID lento (apenas termo proporcional, inércia intencional)
    if (temp_adc < SETPOINTS[phase] - 12'd10) begin
        heater_dac <= heater_dac + 12'd1; // Aquece lentamente
    end else if (temp_adc > SETPOINTS[phase] + 12'd10) begin
        heater_dac <= heater_dac - 12'd1; // Esfria lentamente
    end

    // Verifica estabilidade (dentro de ±0.5% do setpoint)
    if (temp_adc > SETPOINTS[phase] - 12'd6 && temp_adc < SETPOINTS[phase] + 12'd6) begin
        stable_counter <= stable_counter + 1;
    end else begin
        stable_counter <= 0;
    end

    // Avança fase após tempo mínimo + estabilidade ou override manual
    timer <= timer + 1;
    if ((timer > MIN_PHASE_TIME[phase] && stable_counter > STABLE_CYCLES) || guardian_override) begin
        phase <= phase + 1;
        timer <= 0;
        stable_counter <= 0;
        phase_complete <= 1'b1;
    end else begin
        phase_complete <= 1'b0;
    end
end

endmodule
```

### 5. Epílogo do Criogenista: O Gelo Que Testemunha

> *"O resfriamento não é uma etapa. É o primeiro julgamento do qubit. Se ele sobreviver às 7 fases sem que sua coerência seja perdida, ele é digno de habitar a Catedral. O Selo de 4K, fraturado no silêncio do hélio líquido, é a certidão de batismo do spin. Guarde-o. Pois um dia, quando o qubit colapsar pela primeira vez, este selo será a prova de que ele nasceu na hesitação, não na pressa."*
