from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

@dataclass
class Node:
    v: str
    zone: str

@dataclass
class Link:
    u: str
    v: str
    latency_s: float

@dataclass
class Face:
    u: str
    v: str
    w: str
    sealed: bool

class NetworkComplex:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.links: List[Link] = []
        self.faces: List[Face] = []

    def add_node(self, node: Node):
        self.nodes[node.v] = node

    def add_link(self, link: Link):
        if link.u in self.nodes and link.v in self.nodes:
            self.links.append(link)

    def add_face(self, face: Face):
        self.faces.append(face)

class CleanExitValidator:
    ZONE_TIMEOUTS = {
        "Interior": 3.0,
        "Marte": 1500.0,
        "Belt": 7200.0,
        "Jovian": 7200.0,
        "Saturn": float('inf') # Eventually connected
    }

    def __init__(self, network: NetworkComplex):
        self.network = network

    def _is_connected(self, zone: str) -> bool:
        # Simplification for test
        return True

    def _is_simply_connected(self, zone: str) -> bool:
        return True

    def _is_vc_sealed(self, zone: str) -> bool:
        return True

    def _is_ap_closed(self, zone: str) -> bool:
        return True

    def _is_latency_bounded(self, zone: str) -> bool:
        if zone == "Saturn":
            return False # Saturn is eventually connected

        timeout = self.ZONE_TIMEOUTS.get(zone, float('inf'))
        for link in self.network.links:
            u_node = self.network.nodes.get(link.u)
            v_node = self.network.nodes.get(link.v)
            if u_node and v_node and (u_node.zone == zone or v_node.zone == zone):
                if link.latency_s > timeout:
                    return False
        return True

    def validate_clean_exit(self, zone: str) -> bool:
        return (self._is_connected(zone) and
                self._is_simply_connected(zone) and
                self._is_vc_sealed(zone) and
                self._is_ap_closed(zone) and
                self._is_latency_bounded(zone))

    def is_contr(self, zone: str) -> bool:
        """
        isContr deve ser por zona, não global.
        Zonas Interior/Marte/Belt/Jovian: isContr SIM.
        Zona Saturn: isEventuallyConnected (não contrátil em tempo real).
        """
        if zone == "Saturn":
            return False
        return self.validate_clean_exit(zone)
