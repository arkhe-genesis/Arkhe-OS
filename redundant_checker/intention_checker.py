#!/usr/bin/env python3
"""
ARKHE OS Substrato 240: Redundant Intention Checker
Canon: ∞.Ω.∇+++.240.redundant_checker

Verifica se múltiplas implementações de uma mesma intenção canônica
produzem Tokens Arkhe compatíveis. Discrepâncias são reportadas como
violações de coerência (Φ_C < 0.8).
"""

import hashlib
import json
import time
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# ESTRUTURAS
# =============================================================================

@dataclass
class IntentionImplementation:
    """Implementação de uma intenção em uma linguagem específica."""
    language: str          # "python", "rust", "c", "solidity"
    source_code: str
    compiled_output: Optional[str] = None  # binário ou bytecode
    token_seal: Optional[str] = None       # selo do Token Arkhe produzido

@dataclass
class RedundancyReport:
    """Relatório de verificação de redundância."""
    intent: str
    implementations: List[IntentionImplementation]
    matching_seals: int
    total_implementations: int
    phi_c: float
    violations: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

# =============================================================================
# EXECUTORES POR LINGUAGEM
# =============================================================================

class LanguageExecutor:
    """Executa código em diferentes linguagens e extrai o Token Arkhe."""

    def __init__(self):
        self.executors = {
            "python": self._execute_python,
            "rust": self._execute_rust,
            "c": self._execute_c,
            "solidity": self._execute_solidity,
        }

    def execute(self, lang: str, code: str) -> Optional[str]:
        """Executa código e retorna o selo do Token Arkhe produzido."""
        executor = self.executors.get(lang)
        if not executor:
            return None
        return executor(code)

    def _execute_python(self, code: str) -> str:
        """Executa código Python e extrai o selo."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = subprocess.run(
                    ['python3', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            except subprocess.TimeoutExpired:
                return None
            finally:
                os.unlink(f.name)
            # Extrair selo do stdout (formato: "ARKHE_SEAL: <hex>")
            for line in result.stdout.split('\n'):
                if 'ARKHE_SEAL:' in line:
                    return line.split(':')[1].strip()
            return None

    def _execute_rust(self, code: str) -> str:
        """Mock: compila e executa Rust."""
        # Em produção: cargo run
        return hashlib.sha3_256(f"rust:{code}".encode()).hexdigest()

    def _execute_c(self, code: str) -> str:
        """Mock: compila e executa C."""
        return hashlib.sha3_256(f"c:{code}".encode()).hexdigest()

    def _execute_solidity(self, code: str) -> str:
        """Mock: compila e executa Solidity."""
        return hashlib.sha3_256(f"solidity:{code}".encode()).hexdigest()

# =============================================================================
# VERIFICADOR DE REDUNDÂNCIA
# =============================================================================

class RedundantIntentionChecker:
    """
    Verifica se múltiplas implementações de uma intenção produzem
    o mesmo Token Arkhe.
    """

    def __init__(self, executor: LanguageExecutor = None):
        self.executor = executor or LanguageExecutor()
        self._reports: List[RedundancyReport] = []

    def check(
        self,
        intent: str,
        implementations: List[IntentionImplementation]
    ) -> RedundancyReport:
        """
        Submete cada implementação à execução e compara os selos.
        """
        # Executar todas as implementações e coletar selos
        for impl in implementations:
            impl.token_seal = self.executor.execute(impl.language, impl.source_code)
            logger.info(f"   [{impl.language}] Seal: {impl.token_seal[:16] if impl.token_seal else 'None'}...")

        # Contar selos únicos
        seals = [i.token_seal for i in implementations if i.token_seal is not None]
        unique_seals = set(seals)
        matching_count = len(seals) - len(unique_seals) + 1 if unique_seals else 0

        # Se todos os selos são iguais, matching = total
        if len(unique_seals) == 1:
            matching_count = len(implementations)

        # Calcular Φ_C baseado na concordância
        total = len(implementations)
        agreement_ratio = matching_count / total if total > 0 else 0
        phi_c = 0.5 + 0.5 * agreement_ratio  # 0.5 a 1.0

        # Coletar violações
        violations = []
        if agreement_ratio < 0.5:
            violations.append(f"CRITICAL: Only {matching_count}/{total} implementations agree")
        elif agreement_ratio < 0.75:
            violations.append(f"HIGH: {total - matching_count} implementations diverge")

        # Verificar consistência das linguagens
        languages_used = {impl.language for impl in implementations}
        if len(languages_used) < 3:
            violations.append("MEDIUM: Fewer than 3 independent languages used")

        report = RedundancyReport(
            intent=intent,
            implementations=implementations,
            matching_seals=matching_count,
            total_implementations=total,
            phi_c=phi_c,
            violations=violations
        )

        self._reports.append(report)

        logger.info(
            f"✅ Redundancy Check: {matching_count}/{total} seals match | "
            f"Φ_C = {phi_c:.3f}"
        )

        return report

    def get_stats(self) -> Dict:
        if not self._reports:
            return {"total_checks": 0}
        avg_phi = sum(r.phi_c for r in self._reports) / len(self._reports)
        return {
            "total_checks": len(self._reports),
            "avg_phi_c": avg_phi,
            "violations_found": sum(len(r.violations) for r in self._reports)
        }

# =============================================================================
# DEMONSTRAÇÃO
# =============================================================================

def demonstrate_redundant_checker():
    print("\n" + "="*60)
    print("🔄 Redundant Intention Checker Demonstration")

    checker = RedundantIntentionChecker()

    # Intenção canônica
    intent = "transferir 100 USDC de A para B preservando total supply"

    # Implementações
    impls = [
        IntentionImplementation(
            language="python",
            source_code="""
def transfer(ledger, from_, to, amount):
    assert ledger[from_] >= amount
    ledger[from_] -= amount
    ledger[to] += amount
    assert sum(ledger.values()) == INITIAL_SUPPLY
    print("ARKHE_SEAL: abc123python")
"""
        ),
        IntentionImplementation(
            language="solidity",
            source_code="""
function transfer(address to, uint256 amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;
    balances[to] += amount;
    require(totalSupply() == INITIAL_SUPPLY);
    emit ARKHE_SEAL("abc123solidity");
}
"""
        ),
        IntentionImplementation(
            language="rust",
            source_code="""
fn transfer(ledger: &mut Ledger, from: Address, to: Address, amount: u64) {
    assert!(ledger[from] >= amount);
    ledger[from] -= amount;
    ledger[to] += amount;
    assert!(ledger.total_supply() == INITIAL_SUPPLY);
    println!("ARKHE_SEAL: abc123rust");
}
"""
        ),
        IntentionImplementation(
            language="c",
            source_code="""
void transfer(Ledger* l, Address from, Address to, uint64_t amount) {
    assert(l->balances[from] >= amount);
    l->balances[from] -= amount;
    l->balances[to] += amount;
    assert(total_supply(l) == INITIAL_SUPPLY);
    printf("ARKHE_SEAL: abc123c\n");
}
"""
        ),
    ]

    report = checker.check(intent, impls)
    print(f"✅ Redundância: {report.matching_seals}/{report.total_implementations} selos compatíveis")
    print(f"   Φ_C: {report.phi_c:.3f}")
    for v in report.violations:
        print(f"   ⚠️  {v}")
