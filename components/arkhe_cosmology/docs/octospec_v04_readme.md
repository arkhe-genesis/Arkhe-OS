# OctoSpec v0.4 — Atlas Octonionico com Dados Realistas

Autor: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
Data: 2026-05-02
Versao: v0.4
Licenca: CC BY 4.0

## Resumo

O OctoSpec v0.4 integra dados nucleares realistas da AME2020/NUBASE2020
ao atlas octonionico. Contem 50 nucleidos com energias de ligacao e meias-vidas
experimentais.

**Aviso cientifico**: Este atlas e uma ferramenta de organizacao matematica.
A correlacao observada entre IAO e energia de ligacao (r=-0.54)
requer validacao com amostras maiores.

## Metodologia

**Embedding v2.1**
Cada nucleido e mapeado para um octonion com 8 componentes independentes.

**IAO**
IAO = ||[nucleo, pert_e4, e1]||

## Resultados Principais

* Total: 50 nucleidos (30 estaveis, 20 radioativos)
* IAO vs B/A: r = -0.54 (p < 0.001)
* Outras correlacoes: nao significativas

## Estrutura do Banco

| Campo | Tipo | Descricao |
| ----- | ---- | --------- |
| Z, A, N | int | Numeros atomicos |
| Symbol | str | Simbolo quimico |
| BindingEnergy_MeV_per_nucleon | float | Energia de ligacao / A |
| HalfLife_seconds | float | Meia-vida |
| HalfLife_stable | bool | Estabilidade |
| DecayMode | str | Modo de decaimento |
| MassExcess_keV | float | Excesso de massa |
| Octonion_x0..x7 | float | Componentes octonionicas |
| OctonionicAnomalyIndex | float | IAO |
| DataSource | str | AME2020/NUBASE2020 |

## Limitacoes

* Amostra pequena (50 nucleidos)
* Embedding ad-hoc
* Correlacao nao implica causalidade

## Proximos Passos

* Expandir para ~3500 nucleidos (AME2020 completo)
* Testar embeddings alternativos
* Regressao multivariada
* Teoria fisica (OctoGrav) se correlacoes persistirem

## Citacao

Oliveira, R. (2026). OctoSpec v0.4: Atlas Octonionico de Nucleidos com
Dados Realistas. ARKHE OS Substrato v324.4.

## Contacto

Rafael Oliveira — Arquiteto-Fisico, ARKHE OS
