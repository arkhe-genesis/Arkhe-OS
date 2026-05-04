#!/usr/bin/env python3
import json

def cross_validate_cosmology_hardware(cosmo_results_path, hardware_results_path):
    """
    Validação cruzada entre resultados cosmológicos e de hardware.

    Objetivo: verificar consistência entre assinatura topológica
    observada no cosmos e medida em laboratório.
    """
    try:
        with open(cosmo_results_path, 'r') as f:
            cosmology_results = json.load(f)

        with open(hardware_results_path, 'r') as f:
            hardware_results = json.load(f)
    except FileNotFoundError as e:
        print(f"Erro ao carregar arquivos JSON: {e}")
        return None

    # Extrair parâmetros chave
    cosmo_period = cosmology_results.get('bayesian_results', {}).get('posterior_P', None)
    hardware_L = hardware_results.get('specification', {}).get('L_physical', None)

    # Teste de consistência: período cosmológico ≈ L físico do hardware
    if cosmo_period is not None and hardware_L is not None:
        period_match = abs(cosmo_period - hardware_L) < 0.1  # Tolerância de 10%
        print(f"\n🔗 VALIDAÇÃO CRUZADA:")
        print(f"   Período cosmológico P: {cosmo_period:.3f}")
        print(f"   Tamanho de hardware L: {hardware_L:.3f}")
        print(f"   ✅ Consistente" if period_match else "   ⚠️ Inconsistente")
        return period_match
    else:
        print("\n⚠️ Sem período cosmológico ou L de hardware determinado para validação cruzada")
        return None

if __name__ == "__main__":
    cross_validate_cosmology_hardware('planck_torus_results_v299.json', 'mini_merkabah_results_v299.json')
