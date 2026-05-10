import logging
from typing import Optional, Dict, List, Tuple, Any, Set
from .retrocausal_consistency import TemporalConsistencyOracle, TemporalMessage, ConsistencyReport

log = logging.getLogger(__name__)

class HeytingConsistencyOracle(TemporalConsistencyOracle):
    """
    Oráculo de Consistência Temporal estendido com Álgebra de Heyting.

    Implementa:
      - Forcing (p => q): "q é seguro em todos os futuros onde p é verdade"
      - Pseudocomplemento (~p): p => bottom
    """

    def __init__(self, ledger: Any, epsilon_seconds: float = 1.0, quantum_window: float = 1e-12, max_heyting_depth: int = 5):
        super().__init__(ledger, epsilon_seconds, quantum_window)
        self.max_heyting_depth = max_heyting_depth

    def get_futures(self, message_id: str, current_depth: int = 0) -> List[Any]:
        """
        Retorna todos os eventos futuros acessíveis a partir da mensagem p.
        Limitado por current_depth para evitar custo computacional excessivo.
        """
        if current_depth >= self.max_heyting_depth:
            return []

        futures = []
        for rec in self.ledger.get_records():
            # Acessa filhos diretos
            if rec['payload'].get('caused_by') == message_id:
                futures.append(rec)
                futures.extend(self.get_futures(rec['payload'].get('msg_id'), current_depth + 1))
        return futures

    def implies(self, p: TemporalMessage, q: TemporalMessage, visited: Optional[Set[str]] = None) -> bool:
        """
        Implicação de Heyting como Forcing (p => q).

        Semântica de Kripke: p => q é verdade em um estado se para todos os
        estados futuros acessíveis a partir dele, se p é verdade, q também deve ser seguro.

        Para evitar a enumeração total:
        Limitamos a profundidade da busca e usamos memoization (visited).
        """
        if visited is None:
            visited = set()

        # Proteção contra loops
        state_key = f"{p.id}=>{q.id}"
        if state_key in visited:
            return True

        visited.add(state_key)

        # Na prática: q deve ser consistente se p foi emitido.
        # Avaliamos a consistência de p
        p_report = self.evaluate(p)
        if not p_report.consistent:
            return True # Falso implica qualquer coisa

        # Avaliamos q no contexto temporal de p
        # q deve ser consistente (seguro) em todos os futuros acessíveis de p
        q_report = self.evaluate(q)
        if not q_report.consistent:
            return False

        # Verifica futuros causais até max_heyting_depth
        futures = self.get_futures(p.id)

        # Em todos os futuros, q continua sendo válido?
        # (Na simulação simplificada, verificamos apenas se q não entra em loop causal com p ou com seus futuros)
        for f in futures:
            f_mid = f['payload'].get('msg_id')
            if f_mid and self._has_causal_path(q.id, f_mid, depth=self.max_heyting_depth):
                 # q causaria um loop no futuro de p
                 return False

        return True

    def _get_bottom_message(self, source_msg: TemporalMessage) -> TemporalMessage:
        """
        Cria uma mensagem Bottom (⊥) que é intrinsecamente inconsistente.
        Isso é feito criando uma mensagem que entra em loop causal explícito consigo mesma
        ou com o target.
        """
        from .retrocausal_consistency import TemporalMessage as TM
        # Cria um Bottom temporal (target == source) com conteúdo fixo de paradoxo
        return TM(
            id="BOTTOM_PARADOX_000000",
            content="PARADOX",
            source_timestamp=source_msg.source_timestamp,
            target_timestamp=source_msg.source_timestamp - 1000.0, # Passado extremo fora da janela quântica
            sender_seal="BOTTOM",
            receiver_seal="BOTTOM"
        )

    def not_p(self, p: TemporalMessage, visited: Optional[Set[str]] = None) -> bool:
        """
        Pseudocomplemento de Heyting: ~p = p => ⊥

        A avaliação de ~p deve evitar loops infinitos. Para isso, geramos um estado
        Bottom temporário e o validamos com a implicação, repassando o conjunto de visited.
        """
        if visited is None:
            visited = set()

        if f"NOT_{p.id}" in visited:
            return False # Evita loop recursivo na avaliação do pseudocomplemento

        visited.add(f"NOT_{p.id}")

        bottom = self._get_bottom_message(p)
        return self.implies(p, bottom, visited)
