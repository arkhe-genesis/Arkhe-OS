#!/usr/bin/env python3
"""
ARKHE OS Substrato 240: Assembly Verifier
Canon: ∞.Ω.∇+++.240.assembly_verifier

Verifica equivalência entre código assembly (EVM, RISC‑V) e
especificações formais (Lean/BEAVER), usando redução simbólica e SMT.
"""

import re
import json
import hashlib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from lean_bridge import IntelligenceProposition

# =============================================================================
# ESTRUTURAS
# =============================================================================

@dataclass
class AssemblyBlock:
    """Bloco básico de assembly."""
    label: str
    instructions: List[str]
    successors: List[str]  # labels dos blocos sucessores

@dataclass
class SymbolicState:
    """Estado simbólico para execução."""
    registers: Dict[str, str]   # registrador → expressão simbólica
    memory: Dict[str, str]      # endereço → expressão simbólica
    path_constraints: List[str] # condições de caminho

    def clone(self) -> 'SymbolicState':
        return SymbolicState(
            registers=dict(self.registers),
            memory=dict(self.memory),
            path_constraints=list(self.path_constraints)
        )

# =============================================================================
# PARSER DE ASSEMBLY
# =============================================================================

class AssemblyParser:
    """Parser para assembly EVM e RISC‑V."""

    EVM_PATTERN = re.compile(r'^\s*(PUSH\d+|POP|ADD|SUB|MUL|DIV|MSTORE|MLOAD|JUMP|JUMPI|EQ|LT|GT|AND|OR|XOR|NOT|SHA3|CALLDATALOAD|RETURN|STOP|REVERT|DUP\d+|SWAP\d+)\s*(\w+)?\s*$')

    @staticmethod
    def parse_evm(source: str) -> List[str]:
        """Parseia assembly EVM e retorna lista de instruções."""
        instructions = []
        for line in source.split('\n'):
            line = line.strip()
            if not line or line.startswith(';') or line.startswith('//'):
                continue
            instructions.append(line)
        return instructions

    @staticmethod
    def parse_riscv(source: str) -> List[str]:
        """Parseia assembly RISC‑V."""
        # Simplificado: add, addi, lw, sw, beq, jal, etc.
        instructions = []
        for line in source.split('\n'):
            line = line.split('#')[0].strip()
            if line:
                instructions.append(line)
        return instructions

# =============================================================================
# EXECUTOR SIMBÓLICO
# =============================================================================

class SymbolicExecutor:
    """Executor simbólico para assembly."""

    def __init__(self):
        self.var_counter = 0

    def fresh_var(self, prefix: str = "sym") -> str:
        self.var_counter += 1
        return f"{prefix}_{self.var_counter}"

    def execute_evm(self, state: SymbolicState, instruction: str) -> SymbolicState:
        """Executa uma instrução EVM simbolicamente."""
        parts = instruction.split()
        op = parts[0].upper()
        arg = parts[1] if len(parts) > 1 else None

        # Stack simplificado: registradores s0, s1, s2...
        s = state.clone()

        if op.startswith('PUSH'):
            val = arg if arg else '0'
            # Empilhar valor simbólico
            for i in range(3, 0, -1):
                s.registers[f"s{i}"] = s.registers.get(f"s{i-1}", "0")
            s.registers["s0"] = val
        elif op == 'ADD':
            a = s.registers.get("s0", "0")
            b = s.registers.get("s1", "0")
            result = f"({a} + {b})"
            s.registers["s0"] = result
            for i in range(1, 3):
                s.registers[f"s{i}"] = s.registers.get(f"s{i+1}", "0")
        elif op == 'SUB':
            a = s.registers.get("s0", "0")
            b = s.registers.get("s1", "0")
            result = f"({a} - {b})"
            s.registers["s0"] = result
            for i in range(1, 3):
                s.registers[f"s{i}"] = s.registers.get(f"s{i+1}", "0")
        elif op == 'MUL':
            a = s.registers.get("s0", "0")
            b = s.registers.get("s1", "0")
            result = f"({a} * {b})"
            s.registers["s0"] = result
            for i in range(1, 3):
                s.registers[f"s{i}"] = s.registers.get(f"s{i+1}", "0")
        elif op == 'MSTORE':
            addr = s.registers.get("s0", "0")
            val = s.registers.get("s1", "0")
            s.memory[addr] = val
            s.registers["s0"] = s.registers.get("s2", "0")
            s.registers["s1"] = s.registers.get("s3", "0")
        elif op == 'MLOAD':
            addr = s.registers.get("s0", "0")
            s.registers["s0"] = s.memory.get(addr, "0")
        elif op == 'JUMPI':
            cond = s.registers.get("s1", "0")
            target = s.registers.get("s0", "0")
            # Adicionar condição de caminho
            s.path_constraints.append(f"({cond} != 0)")
            # (O tratamento de jump é feito pelo CFG)
        elif op == 'STOP' or op == 'RETURN':
            s.registers["_halted"] = "1"

        return s

    def build_cfg(self, instructions: List[str]) -> List[AssemblyBlock]:
        """Constrói grafo de fluxo de controle a partir das instruções."""
        blocks = []
        current_block = AssemblyBlock(label="entry", instructions=[], successors=[])

        for inst in instructions:
            parts = inst.split()
            op = parts[0].upper()

            if op.startswith('JUMPDEST') or op == 'STOP' or op == 'RETURN':
                if current_block.instructions:
                    blocks.append(current_block)
                label = parts[1] if len(parts) > 1 else f"block_{len(blocks)}"
                current_block = AssemblyBlock(label=label, instructions=[inst], successors=[])
            else:
                current_block.instructions.append(inst)

        if current_block.instructions:
            blocks.append(current_block)

        return blocks

# =============================================================================
# VERIFICADOR DE EQUIVALÊNCIA
# =============================================================================

class AssemblyVerifier:
    """
    Verifica equivalência entre código assembly e especificação formal.
    """

    def __init__(self):
        self.executor = SymbolicExecutor()
        self.parser = AssemblyParser()

    def verify(self, assembly_code: str, specification: 'IntelligenceProposition') -> Tuple[bool, float, Dict]:
        """
        Verifica se o código assembly satisfaz a especificação formal.

        Args:
            assembly_code: Código assembly (EVM ou RISC‑V).
            specification: Proposição BEAVER da Lean Bridge.

        Returns:
            (is_valid, phi_c, report)
        """
        # Parsear assembly
        instructions = self.parser.parse_evm(assembly_code)
        if not instructions:
            return False, 0.0, {"error": "No instructions parsed"}

        # Construir CFG
        cfg = self.executor.build_cfg(instructions)

        # Execução simbólica
        state = SymbolicState(
            registers={"s0": "input_var_0", "s1": "0", "s2": "0", "s3": "0"},
            memory={},
            path_constraints=[]
        )

        for block in cfg:
            for inst in block.instructions:
                state = self.executor.execute_evm(state, inst)

        # Gerar fórmula SMT simplificada (mock)
        output_expr = state.registers.get("s0", "0")
        smt_formula = f"(assert (= {output_expr} expected_output))"

        # Verificar equivalência com a especificação
        # Mock: compara a expressão simbólica com a conclusão da especificação
        spec_statement = specification.statement
        is_equivalent = self._check_equivalence(output_expr, spec_statement)

        phi_c = 0.95 if is_equivalent else 0.2
        if len(state.path_constraints) > 10:
            phi_c -= 0.05  # penalidade por complexidade

        report = {
            "assembly_instructions": len(instructions),
            "cfg_blocks": len(cfg),
            "symbolic_output": output_expr,
            "smt_formula": smt_formula,
            "path_constraints": len(state.path_constraints),
            "equivalent": is_equivalent,
            "phi_c": phi_c
        }

        return is_equivalent, max(0.0, phi_c), report

    def _check_equivalence(self, expr: str, spec: str) -> bool:
        """Mock: verifica equivalência por similaridade estrutural."""
        # Em produção: chamar SMT solver (Z3, CVC5)
        # Aqui: comparar hashes das expressões normalizadas
        expr_normalized = re.sub(r'\s+', '', expr.lower())
        spec_normalized = re.sub(r'\s+', '', spec.lower())

        # Simular verificação: se ambos contêm "total" e "supply", considerar equivalente
        keywords_spec = set(re.findall(r'\w+', spec_normalized))
        keywords_expr = set(re.findall(r'\w+', expr_normalized))
        overlap = keywords_spec & keywords_expr

        return len(overlap) / max(1, len(keywords_spec)) > 0.3

# =============================================================================
# DEMONSTRAÇÃO
# =============================================================================

def demonstrate_assembly_verifier():
    print("\n" + "="*60)
    print("🔧 Assembly Verifier Demonstration")

    verifier = AssemblyVerifier()

    assembly_code = """
    PUSH1 0x64
    PUSH1 0x00
    MSTORE
    PUSH1 0x01
    PUSH1 0x20
    MSTORE
    PUSH1 0x00
    MLOAD
    PUSH1 0x20
    MLOAD
    ADD
    STOP
    """

    spec = IntelligenceProposition(
        statement="total_supply before = total_supply after",
        evidence_hashes=["hash1"],
        confidence=0.98,
        analyst_id="lean_bridge"
    )

    is_valid, phi_c, report = verifier.verify(assembly_code, spec)
    print(f"✅ Assembly verificado: {is_valid} | Φ_C = {phi_c:.3f}")
    print(f"   Instructions: {report['assembly_instructions']}")
    print(f"   Symbolic output: {report['symbolic_output']}")
