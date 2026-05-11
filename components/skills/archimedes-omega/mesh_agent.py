# mesh_agent.py
"""
Módulo de comunicação entre agentes da mesh.
Suporta Blackboard (arquivo compartilhado) e Nostr real.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import time

logger = logging.getLogger(__name__)

try:
    from nostr.key import PrivateKey
    from nostr.relay_manager import RelayManager
    from nostr.event import Event
    NOSTR_LIB_AVAILABLE = True
except ImportError:
    NOSTR_LIB_AVAILABLE = False


class BlackboardAgent:
    """
    Agente que publica conclusões no quadro negro compartilhado.
    """

    def __init__(self, board_path: str = "blackboard.json"):
        self.board_path = Path(board_path)
        self._init_board()

    def _init_board(self):
        """Inicializa o quadro negro se não existir."""
        if not self.board_path.exists():
            self._save_board({
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "messages": []
            })

    def _load_board(self) -> Dict:
        """Carrega o quadro negro."""
        try:
            with open(self.board_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"version": "1.0", "messages": []}

    def _save_board(self, board: Dict):
        """Salva o quadro negro."""
        with open(self.board_path, 'w') as f:
            json.dump(board, f, indent=2, default=str)

    def publish(
        self,
        agent_id: str,
        message: str,
        data: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Publica uma mensagem no quadro negro.
        """
        board = self._load_board()

        # Gerar ID único
        timestamp = datetime.now().isoformat()
        content = f"{agent_id}:{message}:{timestamp}"
        msg_id = hashlib.sha256(content.encode()).hexdigest()[:16]

        message_entry = {
            "id": msg_id,
            "agent": agent_id,
            "timestamp": timestamp,
            "message": message,
            "data": data or {},
            "tags": tags or []
        }

        board["messages"].append(message_entry)
        self._save_board(board)

        logger.info(f"Mensagem publicada: [{agent_id}] {message[:50]}...")

        return msg_id


class NostrAgent:
    """
    Agente para publicação via protocolo Nostr Real.
    """

    def __init__(self, private_key_hex: Optional[str] = None):
        if NOSTR_LIB_AVAILABLE:
            if private_key_hex:
                self.private_key = PrivateKey(bytes.fromhex(private_key_hex))
            else:
                self.private_key = PrivateKey()

            self.relay_manager = RelayManager()
            self.relays = [
                "wss://relay.damus.io",
                "wss://nos.lol",
                "wss://relay.nostr.band"
            ]
            for relay in self.relays:
                self.relay_manager.add_relay(relay)
        else:
            self.private_key = None
            logger.warning("Biblioteca 'nostr' não disponível. Usando modo simulação.")

        self.published_notes = []

    def publish(self, message: str, data: Optional[Dict] = None) -> str:
        """
        Publica uma nota no Nostr.
        """
        content = f"[Archimedes-Ω] {message}"
        if data:
            # Remove objects that are not JSON serializable if any
            clean_data = json.loads(json.dumps(data, default=str))
            content += f"\n\n```json\n{json.dumps(clean_data, indent=2)}\n```"

        if NOSTR_LIB_AVAILABLE and self.private_key:
            event = Event(content=content, public_key=self.private_key.public_key.hex())
            self.private_key.sign_event(event)
            self.relay_manager.publish_event(event)
            time.sleep(1) # Wait for relays
            note_id = event.id
            logger.info(f"[Nostr] Evento real publicado: {note_id}")
        else:
            note_id = hashlib.sha256(content.encode()).hexdigest()
            logger.info(f"[Nostr] Nota simulada: {note_id[:16]}...")

        self.published_notes.append({
            "id": note_id,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        return note_id


# Função de conveniência
def publish_conclusion(
    conclusion: Dict,
    method: str = "blackboard",
    **kwargs
) -> str:
    """
    Publica uma conclusão usando o método especificado.
    """
    if method == "blackboard":
        agent = BlackboardAgent()
        return agent.publish(
            agent_id="Archimedes-Ω",
            message=conclusion.get("interpretation", "Conclusão gerada"),
            data=conclusion,
            tags=["fret", "coherence", "archimedes-omega"]
        )
    elif method == "nostr":
        agent = NostrAgent()
        return agent.publish(
            message=conclusion.get("interpretation", "Conclusão gerada"),
            data=conclusion
        )
    else:
        raise ValueError(f"Método desconhecido: {method}")
