# arkhe_os/banking_ethics_governance/compiler/predicate_to_ucs_compiler.py
"""
Compilador que transforma predicados éticos bancários simbólicos em restrições UCS.
Usa álgebra simbólica para converter lógica booleana em igualdades/ideal membership
sobre ℚ[X], adaptado para regulamentações financeiras.
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from sympy import Symbol, Eq, And, Or, Not, simplify, preorder_traversal
from sympy.logic.boolalg import BooleanFunction, to_cnf
from dataclasses import dataclass

@dataclass
class BankingUCSConstraint:
    """Representação de uma restrição UCS compilada para contexto bancário."""
    constraint_id: str
    ring: str  # "Q[X]" ou "Fq[X]"
    polynomial_expr: str  # Expressão polinomial em formato Zinc+
    ideal_generator: Optional[str]  # Gerador do ideal para ideal membership
    variables: Dict[str, Dict]  # Metadata das variáveis (tipo, bounds, etc.)
    regulatory_reference: str  # Referência à regulamentação (ex: "BCB_RES_4893_ART_12")

    def to_zinc_code(self) -> str:
        """Gera código Zinc+ para esta restrição."""
        code = f"// Banking UCS Constraint: {self.constraint_id}\n"
        code += f"// Ring: {self.ring}\n"
        code += f"// Regulatory Reference: {self.regulatory_reference}\n"

        if self.ideal_generator:
            # Ideal membership: expr ∈ (generator)
            code += f"constraint {self.polynomial_expr} in ideal({self.ideal_generator});\n"
        else:
            # Igualdade estrita: expr == 0
            code += f"constraint {self.polynomial_expr} == 0;\n"

        # Annotations para variáveis
        for var_name, var_meta in self.variables.items():
            code += f"// Variable {var_name}: {var_meta}\n"

        return code + "\n"

class BankingPredicateToUCSCompiler:
    """Compila predicados éticos bancários simbólicos para restrições UCS."""

    def __init__(self, default_ring: str = "Q[X]", default_ideal: str = "0"):
        self.default_ring = default_ring
        self.default_ideal = default_ideal
        self.variable_counter = 0

    def compile_banking_predicate(self, predicate: Any,
                                  context: Dict[str, Symbol]) -> List[BankingUCSConstraint]:
        """
        Compila um predicado ético bancário para uma ou mais restrições UCS.

        Args:
            predicate: Predicado ético bancário com expressão simbólica
            context: Mapeamento de nomes de variáveis → símbolos SymPy

        Returns:
            Lista de restrições UCS equivalentes ao predicado
        """
        if predicate.symbolic_expression is None:
            raise ValueError(f"Predicate {predicate.predicate_id} has no symbolic expression")

        constraints = []

        # Analisa a expressão booleana e converte para forma normal conjuntiva
        cnf_expr = self._to_cnf(predicate.symbolic_expression)

        # Para cada cláusula na CNF, gera uma restrição UCS
        for i, clause in enumerate(self._extract_clauses(cnf_expr)):
            constraint = self._compile_clause_to_banking_ucs(
                clause,
                f"{predicate.predicate_id}_clause_{i}",
                context,
                predicate.parameters,
                predicate.references[0] if predicate.references else "UNKNOWN_REG"
            )
            if constraint:
                constraints.append(constraint)

        return constraints

    def _to_cnf(self, expr: Any) -> Any:
        """Converte expressão para Forma Normal Conjuntiva (CNF)."""
        return to_cnf(expr, simplify=True)

    def _extract_clauses(self, cnf_expr: Any) -> List[Any]:
        """Extrai as cláusulas de uma expressão em CNF."""
        if isinstance(cnf_expr, And):
            return list(cnf_expr.args)
        else:
            return [cnf_expr]

    def _compile_clause_to_banking_ucs(self, clause: Any, constraint_id: str,
                                      context: Dict[str, Symbol], parameters: Dict[str, Any],
                                      regulatory_ref: str) -> BankingUCSConstraint:
        """
        Compila uma cláusula em CNF para uma restrição UCS.
        """
        # Extrair variáveis da cláusula
        variables = {}
        for node in preorder_traversal(clause):
            if isinstance(node, Symbol):
                variables[str(node)] = {"type": "real", "visibility": "private"}

        # Gerar representação em string polinomial (simplificada)
        # Para um compilador real, converteríamos And/Or/Le/Ge para polinômios
        expr_str = str(clause)

        # Limpar a string para formato mais próximo ao Zinc+
        expr_str = expr_str.replace("Abs", "abs").replace("Le", "<=").replace("Ge", ">=").replace("And", "&&").replace("Or", "||")

        return BankingUCSConstraint(
            constraint_id=constraint_id,
            ring=self.default_ring,
            polynomial_expr=f"({expr_str})",
            ideal_generator=self.default_ideal if self.default_ideal != "0" else None,
            variables=variables,
            regulatory_reference=regulatory_ref
        )
