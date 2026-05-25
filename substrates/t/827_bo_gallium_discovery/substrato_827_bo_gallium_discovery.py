import json
import os
import hashlib
import tempfile
import base64

class Substrato827BOGalliumDiscovery:
    def __init__(self):
        self.payload = {
            "id": "827-BO-GALLIUM-DISCOVERY",
            "title": "Bayesian Optimization for Ga-Based Semiconductor Discovery",
            "architect": "ORCID 0009-0005-2697-4668",
            "status": "CANONIZED_PROVISIONAL",
            "version": "1.0",
            "description": "ML-guided Bayesian Optimization with KNN surrogate and SMACT screening for chemical plausibility.",
            "components": [
                {
                    "name": "bo_gallium_discovery.py",
                    "type": "script"
                }
            ]
        }
        self.scripts = {
            "bo_gallium_discovery.py": """#!/usr/bin/env python3
# bo_gallium_discovery.py - Substrato 827 (Research Integration)
# Bayesian Optimization for Ga-Based Semiconductor Discovery
# Based on: ACS Materials Letters (2026) - DOI: 10.1021/acsmaterialslett.5c01482
# Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
#
# Framework: ML-guided Bayesian Optimization with KNN surrogate
#            and SMACT screening for chemical plausibility.

import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import cross_val_score
from skopt import gp_minimize, space
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args
from typing import List, Tuple, Dict, Optional
import json
import hashlib

# SMACT integration (chemical plausibility screening)
try:
    import smact
    from smact.screening import pauling_test
    SMACT_AVAILABLE = True
except ImportError:
    SMACT_AVAILABLE = False
    print("⚠️  SMACT not installed. Install with: pip install smact")


class ChemicalSpace:
    # Define o espaco quimico para composicoes de Ga.

    # Elementos co-eletronicos comuns para semicondutores de Ga
    COELEMENTS = {
        'O': {'ox_states': [-2], 'max_ratio': 4.0},
        'S': {'ox_states': [-2], 'max_ratio': 3.0},
        'Se': {'ox_states': [-2], 'max_ratio': 3.0},
        'Te': {'ox_states': [-2], 'max_ratio': 3.0},
        'N': {'ox_states': [-3], 'max_ratio': 2.0},
        'P': {'ox_states': [-3], 'max_ratio': 2.0},
        'As': {'ox_states': [-3], 'max_ratio': 2.0},
        'Cl': {'ox_states': [-1], 'max_ratio': 3.0},
        'Br': {'ox_states': [-1], 'max_ratio': 3.0},
        'I': {'ox_states': [-1], 'max_ratio': 3.0},
        'F': {'ox_states': [-1], 'max_ratio': 5.0},
    }

    # Ga oxidation states
    GA_OX_STATES = [+1, +2, +3]

    @classmethod
    def get_search_space(cls, max_elements: int = 3) -> List:
        # Retorna o espaco de busca para BO.
        dimensions = []

        # Numero de elementos (Ga + coelementos)
        dimensions.append(Integer(1, max_elements, name='num_coelements'))

        # Co-elementos (indices)
        for i in range(max_elements):
            dimensions.append(Categorical(list(cls.COELEMENTS.keys()), name='coelement_' + str(i)))

        # Razoes estequiometricas
        for i in range(max_elements):
            dimensions.append(Real(0.1, 4.0, name='ratio_' + str(i)))

        # Estado de oxidacao do Ga
        dimensions.append(Categorical(cls.GA_OX_STATES, name='ga_ox_state'))

        return dimensions


class KNNSurrogate:
    # Surrogate model KNN para predicao de band gap.
    # Paper reporta R² = 0.812 como otimo entre multiplos modelos testados.

    def __init__(self, n_neighbors: int = 5, weights: str = 'distance'):
        self.model = KNeighborsRegressor(
            n_neighbors=n_neighbors,
            weights=weights,
            metric='euclidean',
        )
        self.is_trained = False
        self.feature_names = None

    def featurize_composition(self, composition: Dict[str, float]) -> np.ndarray:
        # Extrai features de uma composicao quimica.
        from pymatgen.core import Composition, Element

        # Criar composicao pymatgen
        comp = Composition(composition)

        features = {
            'num_elements': len(composition),
            'ga_fraction': composition.get('Ga', 0),
            'mean_electroneg': np.mean([Element(e).X for e in composition]),
            'std_electroneg': np.std([Element(e).X for e in composition]),
            'mean_atomic_radius': np.mean([Element(e).atomic_radius or 0 for e in composition]),
            'std_atomic_radius': np.std([Element(e).atomic_radius or 0 for e in composition]),
            'mean_ionization': np.mean([Element(e).ionization_energy or 0 for e in composition]),
            'total_electrons': sum([Element(e).Z * composition[e] for e in composition]),
            'molecular_weight': comp.weight,
        }

        return np.array(list(features.values()))

    def train(self, compositions: List[Dict], band_gaps: List[float]):
        # Treina o surrogate com dados existentes.
        X = np.array([self.featurize_composition(c) for c in compositions])
        y = np.array(band_gaps)

        self.model.fit(X, y)
        self.is_trained = True

        # Validar (paper reporta R² = 0.812)
        scores = cross_val_score(self.model, X, y, cv=5, scoring='r2')
        print("[827] KNN Surrogate trained. CV R² = {:.3f} (±{:.3f})".format(scores.mean(), scores.std()))

    def predict(self, composition: Dict[str, float]) -> Tuple[float, float]:
        # Prediz band gap e incerteza (via distancia aos vizinhos).
        if not self.is_trained:
            raise ValueError("Model not trained")

        x = self.featurize_composition(composition).reshape(1, -1)

        # Predicao
        pred = self.model.predict(x)[0]

        # Incerteza: distancia media aos k vizinhos
        distances, _ = self.model.kneighbors(x)
        uncertainty = np.mean(distances[0])

        return pred, uncertainty


class SMACTScreening:
    # Screening de plausibilidade quimica via SMACT.

    @staticmethod
    def check_charge_balance(composition: Dict[str, float],
                              ox_states: Dict[str, int]) -> bool:
        # Verifica balanceamento de cargas.
        total_charge = sum(
            composition[elem] * ox_states.get(elem, 0)
            for elem in composition
        )
        return abs(total_charge) < 0.01  # Tolerancia

    @staticmethod
    def check_elemental_feasibility(composition: Dict[str, float]) -> bool:
        # Verifica se elementos sao viaveis para semicondutores.
        if 'Ga' not in composition or composition['Ga'] <= 0:
            return False

        anions = {'O', 'S', 'Se', 'Te', 'N', 'P', 'As', 'Cl', 'Br', 'I', 'F'}
        has_anion = any(elem in anions for elem in composition)

        return has_anion

    @staticmethod
    def check_physical_plausibility(composition: Dict[str, float]) -> Dict:
        # Verifica plausibilidade fisica.
        from pymatgen.core import Element

        checks = {
            'valid': True,
            'warnings': [],
        }

        # Verificar eletronegatividade
        en_values = [Element(e).X for e in composition if Element(e).X]
        if en_values:
            en_range = max(en_values) - min(en_values)
            if en_range > 2.5:
                checks['warnings'].append("Large electronegativity difference: {:.2f}".format(en_range))

        return checks

    @classmethod
    def screen(cls, composition: Dict[str, float],
               ox_states: Dict[str, int]) -> Tuple[bool, Dict]:
        # Executa screening completo SMACT.
        if not SMACT_AVAILABLE:
            # Fallback simples se SMACT nao instalado
            is_valid = (
                cls.check_elemental_feasibility(composition) and
                cls.check_charge_balance(composition, ox_states)
            )
            return is_valid, {'method': 'fallback'}

        # Usar SMACT nativo
        try:
            from smact.screening import pauling_test

            symbols = list(composition.keys())
            stoichs = [composition[s] for s in symbols]
            ox_states_list = [ox_states.get(s, 0) for s in symbols]

            # Pauling test (charge balance + electronegativity)
            result = pauling_test(symbols, stoichs, ox_states_list)

            details = {
                'pauling_test': result,
                'charge_balance': cls.check_charge_balance(composition, ox_states),
                'elemental_feasibility': cls.check_elemental_feasibility(composition),
                'physical_plausibility': cls.check_physical_plausibility(composition),
            }

            is_valid = result and details['charge_balance'] and details['elemental_feasibility']

            return is_valid, details

        except Exception as e:
            return False, {'error': str(e)}


class BayesianOptimizer:
    # Bayesian Optimization para descoberta inversa de semicondutores de Ga.

    def __init__(self, surrogate: KNNSurrogate,
                 target_band_gap: float,
                 tolerance: float = 0.1):
        self.surrogate = surrogate
        self.target = target_band_gap
        self.tolerance = tolerance
        self.history = []

    def objective(self, composition: Dict[str, float], ga_ox_state: int = 3) -> float:
        # Funcao objetivo para BO.
        # Predicao
        pred, uncertainty = self.surrogate.predict(composition)

        # Erro
        error = abs(pred - self.target)

        # Penalidade para incerteza alta
        uncertainty_penalty = 0.1 * uncertainty

        # SMACT screening
        ox_states = self._infer_ox_states(composition, ga_ox_state)
        is_valid, details = SMACTScreening.screen(composition, ox_states)

        if not is_valid:
            # Penalidade alta para composicao invalida
            validity_penalty = 10.0
        else:
            validity_penalty = 0.0

        total = error + uncertainty_penalty + validity_penalty

        # Registrar
        self.history.append({
            'composition': composition,
            'ga_ox_state': ga_ox_state,
            'prediction': pred,
            'uncertainty': uncertainty,
            'error': error,
            'is_valid': is_valid,
            'total_objective': total,
        })

        return total

    def _infer_ox_states(self, composition: Dict[str, float], ga_ox_state: int = 3) -> Dict[str, int]:
        # Infere estados de oxidacao (simplificado).
        ox_states = {'Ga': ga_ox_state}  # Usar o estado do BO ou default

        for elem in composition:
            if elem == 'Ga':
                continue
            # Estados comuns para anions
            if elem in ['O', 'S', 'Se', 'Te']:
                ox_states[elem] = -2
            elif elem in ['N', 'P', 'As']:
                ox_states[elem] = -3
            elif elem in ['Cl', 'Br', 'I', 'F']:
                ox_states[elem] = -1
            else:
                ox_states[elem] = 0

        return ox_states

    def optimize(self, n_calls: int = 100, n_random_starts: int = 10) -> Dict:
        # Executa otimizacao Bayesiana.
        # Espaco de busca
        space = ChemicalSpace.get_search_space(max_elements=2)

        # Funcao objetivo para skopt
        @use_named_args(space)
        def objective(**params):
            # Converter params para composicao
            composition = self._params_to_composition(params)
            ga_ox_state = int(params.get('ga_ox_state', 3))
            return self.objective(composition, ga_ox_state)

        # Executar BO
        result = gp_minimize(
            objective,
            space,
            n_calls=n_calls,
            n_random_starts=n_random_starts,
            acq_func='EI',  # Expected Improvement
            random_state=42,
        )

        # Melhor resultado
        best_params = {dim.name: val for dim, val in zip(space, result.x)}
        best_composition = self._params_to_composition(best_params)
        best_ga_ox_state = int(best_params.get('ga_ox_state', 3))

        return {
            'best_composition': best_composition,
            'best_ga_ox_state': best_ga_ox_state,
            'best_objective': result.fun,
            'predicted_band_gap': self.surrogate.predict(best_composition)[0],
            'n_calls': n_calls,
            'n_valid': sum(1 for h in self.history if h['is_valid']),
            'history': self.history,
        }

    def _params_to_composition(self, params: Dict) -> Dict[str, float]:
        # Converte parametros do BO para composicao quimica.
        composition = {'Ga': 1.0}  # Base

        num_coelements = params.get('num_coelements', 1)

        for i in range(num_coelements):
            elem = params.get('coelement_' + str(i))
            ratio = params.get('ratio_' + str(i), 1.0)
            if elem:
                composition[elem] = ratio

        return composition


class NumpyFloatEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   BAYESIAN OPTIMIZATION - SUBSTRATO 827                  ║")
    print("║   Ga-Based Semiconductor Discovery | ξM-Field Materials    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\\n📚 Source: ACS Materials Letters (2026)")
    print("   DOI: 10.1021/acsmaterialslett.5c01482")
    print("   Method: KNN surrogate + BO + SMACT screening")

    # Dados de treinamento simulados (paper nao fornece dataset)
    # Usando composicoes conhecidas de semicondutores de Ga
    train_compositions = [
        {'Ga': 2, 'O': 3},      # Ga2O3, Eg ~ 4.9 eV
        {'Ga': 1, 'N': 1},      # GaN, Eg ~ 3.4 eV
        {'Ga': 1, 'As': 1},     # GaAs, Eg ~ 1.4 eV
        {'Ga': 1, 'S': 1},      # GaS, Eg ~ 2.5 eV
        {'Ga': 1, 'Se': 1},     # GaSe, Eg ~ 2.1 eV
        {'Ga': 2, 'S': 3},      # Ga2S3, Eg ~ 2.8 eV
        {'Ga': 2, 'Se': 3},     # Ga2Se3, Eg ~ 2.0 eV
        {'Ga': 1, 'Te': 1},     # GaTe, Eg ~ 1.7 eV
        {'Ga': 2, 'O': 2, 'S': 1},  # Ga2O2S, Eg ~ 3.0 eV
    ]

    train_band_gaps = [4.9, 3.4, 1.4, 2.5, 2.1, 2.8, 2.0, 1.7, 3.0]

    # Treinar surrogate
    print("\\n🔄 Training KNN surrogate...")
    surrogate = KNNSurrogate(n_neighbors=3)
    surrogate.train(train_compositions, train_band_gaps)

    # Otimizar para target = 2.0 eV (regiao de maior SMACT validity)
    target_eg = 2.0
    print("\\n🎯 Target band gap: " + str(target_eg) + " eV")
    print("   (Paper reports increased SMACT validity near 1.5-2.5 eV)")

    optimizer = BayesianOptimizer(surrogate, target_band_gap=target_eg)
    result = optimizer.optimize(n_calls=50, n_random_starts=10)

    print("\\n✅ Optimization complete:")
    print("   Best composition: " + str(result['best_composition']))
    print("   Predicted Eg: {:.2f} eV".format(result['predicted_band_gap']))
    print("   Objective: {:.4f}".format(result['best_objective']))
    print("   Valid compositions: " + str(result['n_valid']) + "/" + str(result['n_calls']))

    # Verificar SMACT
    ox_states = optimizer._infer_ox_states(result['best_composition'], result['best_ga_ox_state'])
    is_valid, details = SMACTScreening.screen(result['best_composition'], ox_states)
    print("\\n🔬 SMACT Screening:")
    print("   Valid: " + str(is_valid))
    print("   Details: " + json.dumps(details, indent=2, cls=NumpyFloatEncoder))

    # Salvar resultado
    output = {
        'substrato': '827',
        'source': 'ACS Materials Letters (2026)',
        'target_band_gap': target_eg,
        'result': result,
        'seal': hashlib.sha3_256(
            json.dumps(result['best_composition'], sort_keys=True, cls=NumpyFloatEncoder).encode()
        ).hexdigest(),
    }

    with open('bo_result_827.json', 'w') as f:
        json.dump(output, f, indent=2, cls=NumpyFloatEncoder)

    print("\\n💾 Result saved to bo_result_827.json")
    print("🔐 Seal: " + str(output['seal'][:16]) + "...")


if __name__ == "__main__":
    main()
"""
        }

    def canonize(self):
        for name, content in self.scripts.items():
            self.payload[name] = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        report_str = json.dumps(self.payload, sort_keys=True)
        seal = hashlib.sha3_256(report_str.encode('utf-8')).hexdigest()
        self.payload["canonical_seal"] = seal

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_827_", text=True)
        with os.fdopen(fd, 'w') as f_out:
            f_out.write(json.dumps(self.payload, ensure_ascii=True, indent=2))

        print("Substrato 827 gerado com sucesso!")
        return path

if __name__ == "__main__":
    sub = Substrato827BOGalliumDiscovery()
    print(sub.canonize())
