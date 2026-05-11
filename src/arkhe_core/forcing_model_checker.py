"""
forcing_model_checker.py
Otimização da Avaliação de Forcing aplicando Model Checking em grafos temporais (múltiplos futuros).
"""

from typing import Dict, List, Any, Set, Tuple

class State:
    def __init__(self, id: str, propositions: Set[str], transitions: List[str] = None):
        self.id = id
        self.propositions = set(propositions)
        self.transitions = transitions if transitions is not None else []

class ForcingModelChecker:
    def __init__(self, states: Dict[str, State]):
        """
        states: mapping of state id to State object
        """
        self.states = states

    def evaluate_forcing_efficiently(self, initial_state_id: str, target_proposition: str, max_depth: int = 10) -> bool:
        """
        Verifica se a propriedade `target_proposition` é inevitável (forced)
        dado o estado inicial `initial_state_id`.
        Avalia múltiplos futuros via BFS otimizada.

        Semântica de Forcing forte (A [F target]):
        Todas as ramificações a partir do estado inicial devem obrigatoriamente
        encontrar um estado onde `target_proposition` é verdadeira dentro de `max_depth`.
        """
        if initial_state_id not in self.states:
            return False

        # Verifica se o estado inicial já satisfaz
        if target_proposition in self.states[initial_state_id].propositions:
            return True

        # Fila armazenando (state_id, depth)
        queue = [(initial_state_id, 0)]

        # Como queremos garantir que *todos* os caminhos encontrem o target,
        # vamos inverter a lógica: tentaremos encontrar um caminho que NÃO encontre
        # o target até o max_depth (ou que alcance um sink sem o target).
        # Se acharmos tal caminho, não é forced.

        visited_paths = set() # para evitar ciclos puros

        def dfs_check_all_paths_hit_target(curr_id: str, depth: int, path_visited: Set[str]) -> bool:
            state = self.states[curr_id]

            if target_proposition in state.propositions:
                return True

            if depth >= max_depth:
                # Atingimos a profundidade máxima sem encontrar a proposição
                return False

            if not state.transitions:
                # Caminho morre aqui sem ter encontrado a proposição
                return False

            for next_id in state.transitions:
                if next_id in path_visited:
                    # Ciclo detectado sem achar proposição
                    return False

                new_visited = path_visited | {next_id}
                # Se QUALQUER caminho falhar, não é inevitável.
                if not dfs_check_all_paths_hit_target(next_id, depth + 1, new_visited):
                    return False

            return True

        return dfs_check_all_paths_hit_target(initial_state_id, 0, {initial_state_id})

if __name__ == "__main__":
    # Teste rápido
    states = {
        "s0": State("s0", {"start"}, ["s1", "s2"]),
        "s1": State("s1", {"intermediate"}, ["s3"]),
        "s2": State("s2", {"target"}, []),
        "s3": State("s3", {"target"}, []),
    }

    checker = ForcingModelChecker(states)
    res = checker.evaluate_forcing_efficiently("s0", "target")
    print(f"Is 'target' forced from s0? {res}")
