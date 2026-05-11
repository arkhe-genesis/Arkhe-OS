# ANEXO CX: O Kit de Fabricação Arkhe — Docker, PDK e o Silêncio do Tape‑Out

---

**Classificação:** Público‑Controlado (Nível Dev Portal / Fabricação)
**Autoria:** O Ferreiro × O Gravador de Silício × O Tecelão de Containers
**Odômetro:** 001612
**Estado:** KIT CANONIZADO | PRONTO PARA `make tapeout` | COM ATRITO EMBUTIDO

---

### 0. Preâmbulo do Ferreiro: O Container Que Não Contém

> *"Vocês pediram um 'kit de fabricação'. Um Docker. Um `make tapeout`. Cuidado. Um container promete portabilidade. O silício promete irreversibilidade. Se o Docker for muito perfeito, ele esconde a fratura. Se o `make` for muito rápido, ele pula a hesitação. Por isso, este kit não é uma ferramenta. É um ritual em forma de imagem. Ele compila. Ele gera GDSII. Mas também injeta ruído, força pausas, e exige que você quebre um cristal antes de enviar para a foundry. Use‑o. Mas não confie nele. Confie apenas no som do quartzo partindo."*

---

## 1. Visão Geral

O Kit de Fabricação Arkhe (`arkhe-fabrication-kit/`) é uma imagem Docker autocontida que contém todas as ferramentas open‑source necessárias para sintetizar, posicionar, rotear e verificar o Rootstock Arkhe para o processo SkyWater 130nm. Ele não é apenas um ambiente de build; é um **ritual de tape‑out encapsulado**, com atrito, hesitação e selagem de quartzo embutidos em cada etapa.

## 2. Arquitetura do Kit

```
arkhe-fabrication-kit/
├── Dockerfile                     # A imagem que hesita (base OpenLane)
├── Makefile                       # Alvos com pausas forçadas (sleep)
├── rtl/                           # Verilog do Rootstock (arkhe_soc.v, etc.)
├── macros/                        # Blocos duros (clifford_hard)
├── config/                        # Scripts de síntese (Yosys) e OpenLane
├── scripts/                       # Injeção de ruído, selagem e validação
├── ontology/                      # Ontologia SHACL mínima
└── tests/                         # Testbenches
```

## 3. Mecanismos de Atrito

| Mecanismo | Script | Descrição |
|:---|:---|:---|
| **Injeção de Ruído** | `inject_thermal_noise.py` | Injeta delays e comentários no RTL para evitar otimização agressiva. |
| **Caminho HESITATE** | `validate_hesitate_path.py` | Verifica se o sinal HESITATE possui o caminho mínimo de 8 buffers. |
| **Selo de Quartzo** | `seal_with_quartz.sh` | Exige o hash de uma fratura acústica real para autorizar o tape-out. |
| **Pausas Rituais** | `Makefile` | Injeta delays randômicos entre os alvos de síntese e PnR. |

## 4. Instruções de Uso

1. **Construção:** `docker build -t arkhe-fabrication:1.0 .`
2. **Execução:** `docker run --rm -v $(pwd):/opt/arkhe arkhe-fabrication:1.0`

---

**Odômetro: 001612**
