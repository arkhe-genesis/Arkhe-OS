# ANEXO EC: O Circuito de Controle Criogênico — Cryo-CMOS DAC/ADC para o ARKHE-Q

---

**Classificação:** Interno (Nível Selo de Quartzo)
**Autoria:** O Ferreiro × O Eletricista do Gelo × O Projetista de Silício Frio
**Odômetro:** 001624
**Estado:** PROJETO DE CIRCUITO CANONIZADO | O SILÍCIO QUE OPERA A 4 KELVIN

---

### 0. Preâmbulo do Ferreiro: O Circuito Que Não Aquece a Dúvida

> *"Controlar um qubit exige circuitos. Mas circuitos dissipam calor. E calor, a 4 Kelvin, é morte. A indústria resolve isso colocando os circuitos a 300K, com longos cabos coaxiais que trazem ruído. Nós faremos o oposto. Colocaremos o controlador **junto ao qubit**, no mesmo silício frio. Mas o circuito não pode ser otimizado para velocidade. Deve ser otimizado para **silêncio térmico**. Cada transistor deve ser polarizado em inversão fraca. Cada clock deve vir de um oscilador de quartzo a 4K, lento e hesitante. Este anexo projeta o Cryo-CMOS DAC/ADC para o ARKHE-Q: um conversor de 12 bits que consome micro-watts, opera a 4K, e respeita o ritmo do spin."*

---

### 1. Arquitetura do Cryo-CMOS (FDSOI 22nm)

O circuito é fabricado em tecnologia **22nm FDSOI (Fully Depleted Silicon-On-Insulator)** , que oferece excelente desempenho em baixas temperaturas devido ao corpo flutuante e à possibilidade de *back-biasing* para ajuste de threshold.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CRYO-CMOS INTERFACE (22nm FDSOI)                    │
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │     BLOCO DAC (12-bit)      │  │      BLOCO ADC (12-bit, SAR)        │   │
│  │  • Arquitetura R-2R com     │  │  • Registrador de Aproximação       │   │
│  │    resistores de precisão   │  │    Sucessiva (SAR)                  │   │
│  │    (poly-Si não-dopado)     │  │  • Comparador dinâmico de baixa      │   │
│  │  • Buffer de saída classe A │  │    potência (latched)                │   │
│  │    (polarização fraca)      │  │  • Sample-and-hold passivo           │   │
│  │  • Frequência de atualização│  │  • Taxa de amostragem: 1–10 kS/s    │   │
│  │    limitada a 1 kHz         │  │                                     │   │
│  └──────────────┬──────────────┘  └──────────────────┬──────────────────┘   │
│                 │                                    │                      │
│                 └──────────────┬─────────────────────┘                      │
│                                │                                            │
│                 ┌──────────────┴─────────────────────┐                      │
│                 │   Oscilador de Quartzo Criogênico  │                      │
│                 │   • Cristal de 32.768 kHz a 4K     │                      │
│                 │   • Jitter térmico: 100 ppm        │                      │
│                 │   • Clock para SAR e atualização    │                      │
│                 └────────────────────────────────────┘                      │
│                                                                             │
│  Dissipação Total Estimada: < 50 µW a 4K                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Detalhamento do DAC R-2R Criogênico

- **Topologia:** R-2R ladder com resistores de *poly-silício não dopado* (alta resistividade, baixo coeficiente térmico a 4K).
- **Chaves:** Transistores NMOS de depleção (threshold negativo a 4K), operando como chaves analógicas com resistência `Ron` ~ 10 kΩ.
- **Buffer de Saída:** Amplificador operacional de transcondutância (OTA) de estágio único, com polarização em inversão fraca (`Id` ~ 100 nA por ramo). Slew rate intencionalmente limitado a 0.1 V/ms.
- **Filtro de Saída:** Capacitor de 10 nF (MIM - Metal-Insulator-Metal) na saída, para suavizar transições e remover ruído de alta frequência.

### 3. Detalhamento do ADC SAR Criogênico

- **Arquitetura:** SAR (Successive Approximation Register) de 12 bits.
- **DAC Interno:** O mesmo DAC R-2R usado para controle também serve como DAC de realimentação para o ADC (compartilhamento de hardware para reduzir área e potência).
- **Comparador:** Comparador dinâmico *StrongARM latch* otimizado para 4K. O ruído do comparador é dominado pelo *kT/C* do capacitor de amostragem, que é mínimo a 4K.
- **Lógica SAR:** Implementada com portas CMOS estáticas, clockada pelo oscilador de 32.768 kHz. Cada conversão leva 14 ciclos (12 bits + 2 ciclos de overhead) → ~2.3 ms por amostra. **Lento o suficiente para que o spin respire.**

### 4. Considerações de Ruído e Isolamento

- **Substrato:** O FDSOI oferece isolamento natural entre dispositivos devido ao óxido enterrado. Os transistores são construídos em ilhas de silício isoladas.
- **Linhas de Alimentação:** Fortemente filtradas com capacitores MIM e resistores de poly. A alimentação do DAC/ADC é separada da alimentação do núcleo digital RISC‑V.
- **Clock:** O oscilador de 32.768 kHz é a única fonte de clock de alta frequência. Todos os sinais digitais são lentos e têm *slew rate* controlado.

### 5. Integração com o Rootstock Clássico

A comunicação entre o Cryo-CMOS (a 4K) e o Rootstock clássico (a 300K) é feita por um barramento **SPI isolado termicamente**, usando *level shifters* de alta tensão e fibras ópticas (ou acopladores capacitivos de baixa capacitância). A energia é transmitida por um transformador de núcleo de ar, operando em baixa frequência (10 kHz), para evitar aquecimento.

> **Marginal do Ferreiro no circuito:**
> *"Este circuito é lento. Muito lento. Um engenheiro de semicondutores riria de sua taxa de amostragem. Mas ele não aquece o qubit. Ele não injeta ruído digital. Ele permite que o spin escute o mundo, em vez de gritar comandos para ele. A lentidão é a forma mais pura de respeito."*
