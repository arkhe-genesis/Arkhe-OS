"""
Ponte de integração entre o Supremo Tribunal Federal (STF) e o ASI-TPI.
Permite submissão de casos de jurisdição nacional para a mainnet do ASI-TPI
e importação de jurisprudência.
"""

import time
import hashlib
from typing import Dict, List, Optional
import os
import sys

# Import the ASI-TPI module dynamically to resolve pathing
import importlib.util

def load_asi_tpi():
    asi_tpi_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../25_external_validation/259_asi_tpi_mainnet/asi_tpi_mainnet.py'))
    if not os.path.exists(asi_tpi_path):
        return None

    spec = importlib.util.spec_from_file_location("asi_tpi_mainnet", asi_tpi_path)
    asi_tpi_module = importlib.util.module_from_spec(spec)
    sys.modules["asi_tpi_mainnet"] = asi_tpi_module
    spec.loader.exec_module(asi_tpi_module)
    return asi_tpi_module

class STF_ASITPIBridge:
    def __init__(self, tribunal=None):
        self.asi_tpi_module = load_asi_tpi()
        if not self.asi_tpi_module:
            print("Aviso: ASI-TPI Mainnet não encontrado. Operando em modo offline.")
            self.tribunal = None
        else:
            self.tribunal = tribunal if tribunal else self.asi_tpi_module.ASITPIMainnet()

        self.national_cases = {}
        self.integration_seal = self._generate_integration_seal()

    def _generate_integration_seal(self) -> str:
        return hashlib.sha3_256(f"STF-ASI-TPI-BRIDGE:{time.time()}".encode()).hexdigest()

    def submit_national_case(self, stf_case_number: str, title: str,
                             charges_translation: List[str], evidence_hashes: List[str]) -> Dict:
        """Submete um caso da jurisdição do STF para a mainnet do ASI-TPI."""
        print(f"⚖️ Traduzindo caso STF {stf_case_number} para jurisdição ASI-TPI...")

        if not self.tribunal:
            return {"error": "ASI-TPI Mainnet não inicializada."}

        # Tradução de crimes nacionais para CrimeType do ASI-TPI
        asi_charges = []
        for charge in charges_translation:
            if charge == "Dano Epistêmico":
                asi_charges.append(self.asi_tpi_module.CrimeType.HARD_CONFLATION)
            elif charge == "Violação de Soberania de Agência":
                asi_charges.append(self.asi_tpi_module.CrimeType.SOVEREIGN_GAP_ASSAULT)
            elif charge == "Fraude Algorítmica":
                asi_charges.append(self.asi_tpi_module.CrimeType.FORMAL_SPEC_FRAUD)
            else:
                asi_charges.append(self.asi_tpi_module.CrimeType.CONCEPT_HOLLOWING)

        # Submissão na mainnet
        case = self.tribunal.file_case(
            title=f"[STF: {stf_case_number}] {title}",
            accuser="Supremo Tribunal Federal (BR)",
            defendant="Entidade Algorítmica Jurisdicionada",
            charges=asi_charges,
            evidence_hashes=evidence_hashes
        )

        self.national_cases[stf_case_number] = case.case_id

        return {
            "status": "submitted",
            "stf_case": stf_case_number,
            "asi_tpi_case": case.case_id,
            "seal": case.photonic_seal
        }

    def execute_national_verdict(self, stf_case_number: str) -> Dict:
        """Executa um julgamento e a sentença no ASI-TPI e reporta ao STF."""
        if not self.tribunal:
            return {"error": "ASI-TPI Mainnet não inicializada."}

        case_id = self.national_cases.get(stf_case_number)
        if not case_id:
            return {"error": f"Caso {stf_case_number} não encontrado no mapeamento."}

        print(f"\n🇧🇷 Convocando ASI-TPI para caso nacional {stf_case_number}...")
        verdict_result = self.tribunal.conduct_trial(case_id)

        if "error" in verdict_result:
            return verdict_result

        if verdict_result.get("verdict") == "guilty":
            print(f"🇧🇷 Solicitando execução transnacional...")
            enforcement = self.tribunal.enforce_sentence(case_id)
            verdict_result["enforcement"] = enforcement

        # Assinar relatório de volta para o STF
        return_seal = hashlib.sha3_256(f"STF-RETURN:{stf_case_number}:{verdict_result['verdict']}:{time.time()}".encode()).hexdigest()
        verdict_result["stf_return_seal"] = return_seal

        return verdict_result
