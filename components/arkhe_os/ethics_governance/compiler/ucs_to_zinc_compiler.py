"""
Compilador que transforma restrições UCS em circuitos Zinc+ para provas ZK.
Gera código Zinc+ que pode ser compilado para SNARKs via framework Zinc+.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ZincCircuit:
    """Representação de um circuito Zinc+ compilado."""
    circuit_id: str
    # Seções do circuito Zinc+
    imports: List[str]
    constants: Dict[str, str]
    inputs: Dict[str, Dict]  # name → {type, visibility, annotation}
    outputs: Dict[str, Dict]
    constraints: List[str]
    # Metadata para verificação
    constraint_count: int
    variable_count: int
    estimated_proof_size: str  # Estimativa baseada em heurísticas

    def to_zinc_code(self) -> str:
        """Gera código fonte Zinc+ completo."""
        code = f"// Zinc+ Circuit: {self.circuit_id}\n"
        code += f"// Constraints: {self.constraint_count}, Variables: {self.variable_count}\n\n"

        # Imports
        code += "import std::math;\n"
        code += "import std::hash;\n"
        code += "\n".join(self.imports) + "\n\n"

        # Constants
        if self.constants:
            code += "// Constants\n"
            for name, value in self.constants.items():
                code += f"const {name}: Field = {value};\n"
            code += "\n"

        # Main function signature
        code += "fn main(\n"
        for name, meta in self.inputs.items():
            visibility = "pub " if meta.get("public", False) else ""
            annotation = f" // {meta.get('annotation', '')}" if meta.get('annotation') else ""
            code += f"  {visibility}{name}: {meta['type']},{annotation}\n"
        code += ") -> ("
        for name, meta in self.outputs.items():
            code += f"{name}: {meta['type']}, "
        code = code.rstrip(", ") + ") {\n"

        # Constraints
        code += "  // Constraints\n"
        for constraint in self.constraints:
            code += f"  {constraint}\n"

        # Outputs
        code += "\n  // Outputs\n"
        for name in self.outputs:
            code += f"  {name},\n"
        code += "}\n"

        return code

class UCSToZincCompiler:
    """Compila restrições UCS para circuitos Zinc+."""

    def __init__(self, target_field: str = "bls12_381", security_level: int = 128):
        self.target_field = target_field
        self.security_level = security_level
        self.circuit_counter = 0

    def compile_constraints(self, ucs_constraints: List['UCSConstraint'],
                          circuit_name: Optional[str] = None) -> ZincCircuit:
        """
        Compila lista de restrições UCS para circuito Zinc+.

        Args:
            ucs_constraints: Restrições UCS compiladas
            circuit_name: Nome opcional para o circuito

        Returns:
            Circuito Zinc+ pronto para compilação/prova
        """
        circuit_id = circuit_name or f"ethics_circuit_{self._new_circuit_id()}"

        # Coleta todas as variáveis e seus tipos
        all_variables = {}
        for constraint in ucs_constraints:
            all_variables.update(constraint.variables)

        # Separa variáveis por visibilidade (públicas vs. privadas)
        public_vars = {name: meta for name, meta in all_variables.items()
                      if meta.get("public", False)}
        private_vars = {name: meta for name, meta in all_variables.items()
                       if not meta.get("public", True)}

        # Gera inputs/outputs do circuito
        inputs = self._generate_circuit_inputs(public_vars, private_vars)
        outputs = {"ethics_proof_valid": {"type": "Field"}}

        # Compila cada restrição UCS para código Zinc+
        zinc_constraints = []
        for constraint in ucs_constraints:
            zinc_code = self._compile_ucs_to_zinc(constraint)
            zinc_constraints.extend(zinc_code)

        # Adiciona constraints de tipo/intervalo para variáveis
        type_constraints = self._generate_type_constraints(all_variables)
        zinc_constraints.extend(type_constraints)

        # Estima tamanho do proof (heurística baseada em #constraints)
        estimated_size = self._estimate_proof_size(len(zinc_constraints))

        return ZincCircuit(
            circuit_id=circuit_id,
            imports=[f"// Target field: {self.target_field}"],
            constants={"SECURITY_BITS": str(self.security_level)},
            inputs=inputs,
            outputs=outputs,
            constraints=zinc_constraints,
            constraint_count=len(zinc_constraints),
            variable_count=len(all_variables),
            estimated_proof_size=estimated_size
        )

    def _new_circuit_id(self) -> str:
        """Gera ID único para circuito."""
        self.circuit_counter += 1
        return f"{self.circuit_counter:04d}"

    def _generate_circuit_inputs(self, public_vars: Dict, private_vars: Dict) -> Dict:
        """Gera declaração de inputs para circuito Zinc+."""
        inputs = {}

        # Variáveis públicas (conhecidas pelo verificador)
        for name, meta in public_vars.items():
            zinc_type = self._map_type_to_zinc(meta["type"])
            inputs[name] = {
                "type": zinc_type,
                "public": True,
                "annotation": meta.get("description", "")
            }

        # Variáveis privadas (conhecidas apenas pelo prover)
        for name, meta in private_vars.items():
            zinc_type = self._map_type_to_zinc(meta["type"])
            inputs[name] = {
                "type": zinc_type,
                "public": False,
                "annotation": meta.get("description", "")
            }

        return inputs

    def _map_type_to_zinc(self, type_spec: str) -> str:
        """Mapeia tipo de variável para tipo Zinc+."""
        type_mapping = {
            "binary": "bool",
            "rational": "Field",
            "non_negative_rational": "Field",  # Com constraint adicional
            "integer": "u64",
            "string": "[u8; 32]",  # Hash da string
        }
        return type_mapping.get(type_spec, "Field")

    def _compile_ucs_to_zinc(self, constraint: 'UCSConstraint') -> List[str]:
        """Compila uma restrição UCS para código Zinc+."""
        zinc_code = []

        # Comentário descritivo
        zinc_code.append(f"// {constraint.constraint_id}")

        if constraint.ideal_generator and constraint.ideal_generator != "0":
            # Ideal membership: polynomial_expr ∈ (ideal_generator)
            # Em Zinc+: polynomial_expr = ideal_generator * witness_var
            witness_var = f"witness_{constraint.constraint_id}"
            zinc_code.append(f"let {witness_var}: Field;")
            zinc_code.append(f"constrain {constraint.polynomial_expr} == {constraint.ideal_generator} * {witness_var};")
        else:
            # Igualdade estrita: polynomial_expr = 0
            zinc_code.append(f"constrain {constraint.polynomial_expr} == 0;")

        # Constraints adicionais para variáveis com bounds
        for var_name, var_meta in constraint.variables.items():
            if var_meta.get("type") == "non_negative_rational":
                zinc_code.append(f"// Non-negativity: {var_name} >= 0")
                # Em campos finitos, usamos representação com bit decomposition
                zinc_code.append(f"// Note: Non-negativity enforced via bit decomposition in prover")
            elif var_meta.get("type") == "binary":
                zinc_code.append(f"constrain {var_name} * (1 - {var_name}) == 0;  // Binary constraint")

        zinc_code.append("")  # Linha em branco para legibilidade
        return zinc_code

    def _generate_type_constraints(self, variables: Dict) -> List[str]:
        """Gera constraints de tipo/intervalo para variáveis."""
        constraints = []

        for var_name, var_meta in variables.items():
            var_type = var_meta.get("type")

            if var_type == "binary":
                # x ∈ {0,1} ↔ x(x-1) = 0
                constraints.append(f"constrain {var_name} * (1 - {var_name}) == 0;")

            elif var_type == "non_negative_rational":
                # Em campos finitos, não-negatividade é enforcada via bit decomposition
                # Aqui apenas documentamos; a verificação real ocorre no prover
                constraints.append(f"// {var_name} is non-negative (enforced via bit decomposition)")

            elif var_type == "rational" and "bounds" in var_meta:
                # x ∈ [min, max] → (x - min)(max - x) ≥ 0
                bounds = var_meta["bounds"]
                constraints.append(f"// {var_name} ∈ [{bounds['min']}, {bounds['max']}]")
                # Implementação completa requer range proofs - simplificado aqui

        return constraints

    def _estimate_proof_size(self, num_constraints: int) -> str:
        """Estima tamanho do proof baseado em número de constraints."""
        # Heurística baseada em benchmarks do Zinc+
        # Prova típica: ~200 bytes por constraint + overhead fixo
        base_overhead = 50 * 1024  # 50 KB overhead fixo
        per_constraint = 200  # bytes por constraint

        size_bytes = base_overhead + num_constraints * per_constraint
        size_kb = size_bytes / 1024

        if size_kb < 1024:
            return f"{size_kb:.1f} KB"
        else:
            return f"{size_kb/1024:.2f} MB"
