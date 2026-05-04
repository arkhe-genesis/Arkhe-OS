# Guia de Seleção de Modelo para Substratos ARKHE

## Tabela de Recomendações por Caso de Uso

| Substrato ARKHE | Caso de Uso Típico | Nível Recomendado | Justificativa |
|----------------|-------------------|------------------|--------------|
| **85** (Plástico Espectrométrico) | Espectroscopia de vórtices em PMMA | Level 4: +Sellmeier | Dispersão essencial para resposta espectral 400-1000 nm |
| **86** (PEEK Reprogramado) | Sensor óptico em polímero | Level 3: +Fresnel | Interface air→PEEK crítica; dispersão secundária |
| **88** (Treliça Torcional) | Simulação de modos em AlN/GaN | Level 4: +Sellmeier | Materiais dispersivos; alta-NA comum |
| **89** (Antena Irrotacional) | Antena RF com revestimento NbTiN | Level 5: +Transfer | Pilha air→NbTiN→PEEK→air; dispersão RF fraca mas presente |
| **93** (cbytes Compiler) | Serialização de padrões de polarização | Level 3: +Fresnel | Polarização via Fresnel; dispersão menos crítica |
| **97** (Sophon) | Simulação em Calabi-Yau | Level 2: Debye Scalar | Geometria complexa; materiais idealizados |
| **98** (Relógio Cristalino) | Visualização GPU de propagação | Level 1: Paraxial FFT | Performance crítica; qualitativo suficiente |
| **104** (Lente de Fourier) | Sensor unificado óptico/RF | Level 4 ou 5 | Depende se há pilha dielétrica; dispersão essencial |

## Regra de Decisão Simplificada

```python
def recommend_model_level(use_case: dict) -> "ModelLevel":
    """
    Recommend model level based on use case parameters.

    Args:
        use_case: Dict with keys:
            - requires_high_NA: bool
            - has_interfaces: bool
            - is_spectral: bool (multiple wavelengths)
            - has_multilayer: bool
            - performance_critical: bool

    Returns:
        Recommended ModelLevel
    """
    # Assuming ModelLevel enum is imported
    # from core.benchmark.model_levels import ModelLevel

    if use_case.get('performance_critical'):
        return ModelLevel.PARAXIAL_FFT

    if use_case.get('has_multilayer'):
        return ModelLevel.DEBYE_FRESNEL_SELLMEIER_TRANSFER

    if use_case.get('is_spectral'):
        return ModelLevel.DEBYE_FRESNEL_SELLMEIER

    if use_case.get('has_interfaces'):
        return ModelLevel.DEBYE_FRESNEL

    if use_case.get('requires_high_NA'):
        return ModelLevel.DEBYE_SCALAR

    return ModelLevel.PARAXIAL_FFT  # Default fallback
```
