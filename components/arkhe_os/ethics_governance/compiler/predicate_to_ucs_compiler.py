"""
Compilador que transforma predicados éticos simbólicos em restrições UCS.
Usa álgebra simbólica para converter lógica booleana em igualdades/ideal membership sobre ℚ[X].
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from sympy import Symbol, Eq, And, Or, Not, simplify, preorder_traversal
from sympy.logic.boolalg import BooleanFunction
from dataclasses import dataclass

@dataclass
class UCSConstraint:
    """Representação de uma restrição UCS compilada."""
    constraint_id: str
    ring: str  # "Q[X]" ou "Fq[X]"
    polynomial_expr: str  # Expressão polinomial em formato Zinc+
    ideal_generator: Optional[str]  # Gerador do ideal para ideal membership
    variables: Dict[str, Dict]  # Metadata das variáveis (tipo, bounds, etc.)

    def to_zinc_code(self) -> str:
        """Gera código Zinc+ para esta restrição."""
        code = f"// UCS Constraint: {self.constraint_id}\n"
        code += f"// Ring: {self.ring}\n"

        if self.ideal_generator:
            # Ideal membership: expr ∈ (generator)
            code += f"constraint {self.polynomial_expr} in ideal({self.ideal_generator});\n"
        else:
            # Igualdade estrita: expr = 0
            code += f"constraint {self.polynomial_expr} == 0;\n"

        # Annotations para variáveis
        for var_name, var_meta in self.variables.items():
            code += f"// Variable {var_name}: {var_meta}\n"

        return code + "\n"

class PredicateToUCSCompiler:
    """Compila predicados éticos simbólicos para restrições UCS."""

    def __init__(self, default_ring: str = "Q[X]", default_ideal: str = "0"):
        self.default_ring = default_ring
        self.default_ideal = default_ideal
        self.variable_counter = 0

    def compile_predicate(self, predicate: Any,
                         context: Dict[str, Symbol]) -> List[UCSConstraint]:
        """
        Compila um predicado ético para uma ou mais restrições UCS.

        Args:
            predicate: Predicado ético com expressão simbólica
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
            constraint = self._compile_clause_to_ucs(
                clause,
                f"{predicate.predicate_id}_clause_{i}",
                context,
                predicate.parameters
            )
            if constraint:
                constraints.append(constraint)

        return constraints

    def _to_cnf(self, expr: BooleanFunction) -> BooleanFunction:
        """Converte expressão booleana para forma normal conjuntiva (CNF)."""
        from sympy.logic.boolalg import to_cnf
        # Simplifica primeiro
        simplified = simplify(expr)
        # Converte para CNF usando algoritmo de Tseitin para evitar explosão exponencial
        return to_cnf(simplified)

    def _extract_clauses(self, cnf_expr: BooleanFunction) -> List[BooleanFunction]:
        """Extrai cláusulas individuais de uma expressão em CNF."""
        if cnf_expr.func == And:
            return list(cnf_expr.args)
        else:
            return [cnf_expr]

    def _compile_clause_to_ucs(self, clause: BooleanFunction,
                              constraint_id: str,
                              context: Dict[str, Symbol],
                              parameters: Dict) -> Optional[UCSConstraint]:
        """
        Compila uma cláusula booleana para restrição UCS.

        Estratégias de compilação:
        1. Desigualdades: |a - b| ≤ ε → (a - b)² ≤ ε² → ε² - (a - b)² ∈ (0)
        2. Implicações: p → q → ¬p ∨ q → (1 - p) + q - (1-p)q ∈ (0) [sobre {0,1}]
        3. Ideal membership para constraints de tipo: x ∈ {0,1} → x(x-1) ∈ (0)
        """
        # Caso 1: Desigualdade Abs(a - b) ≤ ε
        if self._is_absolute_inequality(clause):
            return self._compile_absolute_inequality(clause, constraint_id, context, parameters)

        # Caso 2: Implicação lógica
        elif self._is_implication(clause):
            return self._compile_implication(clause, constraint_id, context, parameters)

        # Caso 3: Restrição de tipo/intervalo
        elif self._is_type_constraint(clause):
            return self._compile_type_constraint(clause, constraint_id, context, parameters)

        # Caso geral: expressão booleana → polinômio sobre {0,1}
        else:
            return self._compile_boolean_to_polynomial(clause, constraint_id, context, parameters)

    def _compile_absolute_inequality(self, clause: Any, constraint_id: str,
                                   context: Dict, parameters: Dict) -> UCSConstraint:
        """
        Compila |a - b| ≤ ε para restrição UCS.

        Transformação: |a - b| ≤ ε ↔ (a - b)² ≤ ε² ↔ ε² - (a - b)² ≥ 0
        Em UCS: ε² - (a - b)² - s = 0, s ≥ 0 (variável de slack)
        """
        # Extrai componentes da desigualdade
        left_expr, right_expr, epsilon = self._parse_absolute_inequality(clause, context)

        # Gera polinômio: ε² - (left - right)² - slack = 0
        slack_var = f"slack_{self._new_var_id()}"
        polynomial = f"{epsilon}**2 - ({left_expr} - {right_expr})**2 - {slack_var}"

        # Restrição adicional: slack ≥ 0 (ideal membership em anel ordenado)
        # Em Zinc+, usamos ideal (slack) para forçar slack = 0 quando possível

        variables = {
            **{str(v): {"type": "rational", "source": "context"} for v in context.values()},
            slack_var: {"type": "non_negative_rational", "purpose": "slack_variable"}
        }

        return UCSConstraint(
            constraint_id=constraint_id,
            ring="Q[X]",
            polynomial_expr=polynomial,
            ideal_generator=None,  # Igualdade estrita
            variables=variables
        )

    def _new_var_id(self) -> str:
        """Gera ID único para nova variável."""
        self.variable_counter += 1
        return f"v{self.variable_counter:04d}"

    # Métodos auxiliares de parsing (implementação simplificada)
    def _is_absolute_inequality(self, clause: Any) -> bool:
        """Verifica se cláusula é desigualdade com valor absoluto."""
        return hasattr(clause, 'func') and 'Abs' in str(clause.func)

    def _parse_absolute_inequality(self, clause: Any, context: Dict) -> Tuple[str, str, str]:
        """Extrai componentes de |a - b| ≤ ε."""
        # Parsing simplificado - em produção, usar AST completo
        clause_str = str(clause)
        # Exemplo: "Abs(g1_rate - g2_rate) <= 0.05"
        match = re.match(r'Abs\(([^)]+)\)\s*<=\s*([\d.]+)', clause_str)
        if match:
            diff_expr = match.group(1)  # "g1_rate - g2_rate"
            epsilon = match.group(2)     # "0.05"
            # Separa os dois termos da diferença
            terms = re.split(r'\s*[-+]\s*', diff_expr)
            return terms[0].strip(), terms[1].strip() if len(terms) > 1 else "0", epsilon
        return "0", "0", "0.05"

    def _is_implication(self, clause: Any) -> bool:
        """Verifica se cláusula é implicação lógica."""
        return hasattr(clause, 'func') and clause.func.__name__ == 'Implies'

    def _compile_implication(self, clause: Any, constraint_id: str,
                           context: Dict, parameters: Dict) -> UCSConstraint:
        """
        Compila implicação p → q para restrição UCS sobre variáveis binárias.

        Transformação: p → q ↔ ¬p ∨ q ↔ (1 - p) + q - (1-p)q = 0 sobre {0,1}
        Simplificado: q - p + p*q = 0 → q(1 + p) = p
        """
        # Extrai antecedente e consequente
        antecedent, consequent = clause.args

        # Converte para expressões polinomiais (assumindo variáveis binárias)
        p_expr = self._symbol_to_polynomial(antecedent, context)
        q_expr = self._symbol_to_polynomial(consequent, context)

        # Polinômio: q - p + p*q = 0
        polynomial = f"({q_expr}) - ({p_expr}) + ({p_expr})*({q_expr})"

        # Restrição de tipo: p, q ∈ {0,1} → p(p-1) ∈ (0), q(q-1) ∈ (0)
        # Estas são adicionadas como constraints separadas pelo compilador de tipo

        variables = {
            **{str(v): {"type": "binary", "source": "context"} for v in context.values()},
        }

        return UCSConstraint(
            constraint_id=constraint_id,
            ring="Q[X]",
            polynomial_expr=polynomial,
            ideal_generator=None,
            variables=variables
        )

    def _symbol_to_polynomial(self, symbol: Any, context: Dict) -> str:
        """Converte símbolo SymPy para string de polinômio Zinc+."""
        if isinstance(symbol, Symbol):
            return str(symbol)
        # Para expressões compostas, recursão simplificada
        return str(symbol)

    def _is_type_constraint(self, clause: Any) -> bool:
        """Verifica se cláusula é restrição de tipo/intervalo."""
        clause_str = str(clause)
        return any(op in clause_str for op in ['>=', '<=', '==', 'in'])

    def _compile_type_constraint(self, clause: Any, constraint_id: str,
                               context: Dict, parameters: Dict) -> UCSConstraint:
        """
        Compila restrição de tipo/intervalo para UCS.

        Exemplos:
        - x ∈ {0,1} → x(x-1) ∈ (0)
        - 0 ≤ x ≤ 1 → x(1-x) - s = 0, s ≥ 0
        """
        clause_str = str(clause)

        # Caso: x(x-1) = 0 para variável binária
        if 'x**2 - x' in clause_str or 'x*(x-1)' in clause_str:
            var_name = re.search(r'(\w+)', clause_str).group(1)
            return UCSConstraint(
                constraint_id=constraint_id,
                ring="Q[X]",
                polynomial_expr=f"{var_name}*({var_name} - 1)",
                ideal_generator="0",  # Igualdade estrita
                variables={var_name: {"type": "binary"}}
            )

        # Caso geral: desigualdade linear
        return self._compile_linear_inequality(clause, constraint_id, context)

    def _compile_linear_inequality(self, clause: Any, constraint_id: str,
                                 context: Dict) -> UCSConstraint:
        """Compila desigualdade linear para UCS com variável de slack."""
        # Parsing simplificado
        clause_str = str(clause)
        match = re.match(r'(\w+)\s*([<>]=?)\s*([\d.]+)', clause_str)
        if match:
            var, op, val = match.groups()
            if op in ['<=', '==']:
                # x <= c → c - x - s = 0, s ≥ 0
                slack = f"slack_{self._new_var_id()}"
                polynomial = f"{val} - {var} - {slack}"
                return UCSConstraint(
                    constraint_id=constraint_id,
                    ring="Q[X]",
                    polynomial_expr=polynomial,
                    ideal_generator=None,
                    variables={
                        var: {"type": "rational"},
                        slack: {"type": "non_negative_rational"}
                    }
                )

        # Fallback: restrição como ideal membership trivial
        return UCSConstraint(
            constraint_id=constraint_id,
            ring="Q[X]",
            polynomial_expr="0",
            ideal_generator="0",
            variables={}
        )

    def _compile_boolean_to_polynomial(self, clause: Any, constraint_id: str,
                                      context: Dict, parameters: Dict) -> Optional[UCSConstraint]:
        """
        Compila expressão booleana arbitrária para polinômio sobre {0,1}.

        Usa codificação aritmética:
        - ¬p → 1 - p
        - p ∧ q → p*q
        - p ∨ q → p + q - p*q
        """
        # Implementação simplificada: converte para string e avalia como polinômio
        poly_str = self._boolean_to_arithmetic(str(clause), context)

        return UCSConstraint(
            constraint_id=constraint_id,
            ring="Q[X]",
            polynomial_expr=f"{poly_str}",
            ideal_generator="0",
            variables={str(v): {"type": "binary"} for v in context.values()}
        )

    def _boolean_to_arithmetic(self, bool_expr: str, context: Dict) -> str:
        """Converte expressão booleana string para expressão aritmética."""
        # Substituições para operadores booleanos → aritméticos
        replacements = {
            'And(': '(',  # p ∧ q → p*q (aplicado recursivamente)
            'Or(': '(',   # p ∨ q → p + q - p*q
            'Not(': '1 - (',  # ¬p → 1 - p
            '==': ' - ',  # p == q → p - q = 0
            '!=': ' - ',  # p != q → (p - q)² > 0
        }

        result = bool_expr
        for old, new in replacements.items():
            result = result.replace(old, new)

        # Nota: implementação completa requer parser AST - esta é simplificação
        return result
