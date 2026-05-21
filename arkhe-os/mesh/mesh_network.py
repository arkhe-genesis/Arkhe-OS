# =========================================================
# Simulador de Rede Mesh Mundial
# Substrato 397
# =========================================================
import random, math, time
from typing import Dict, List, Tuple, Optional
from mesh.smartphone_node import SmartphoneNode, ParticleType, Event

class MeshNetwork:
    def __init__(self, n_nodes: int = 1000, world_coverage: bool = True):
        self.n_nodes = n_nodes
        self.nodes: Dict[int, SmartphoneNode] = {}
        self.global_events: List[Event] = []
        self.coincident_events: List[List[Event]] = []

        for i in range(n_nodes):
            if world_coverage:
                lat = random.uniform(-90, 90)
                lon = random.uniform(-180, 180)
            else:
                lat = random.gauss(40.7, 10)
                lon = random.gauss(-74.0, 10)

            self.nodes[i] = SmartphoneNode(node_id=i, lat=lat, lon=lon)

        self._build_neighborhoods()

    def _build_neighborhoods(self, max_neighbors: int = 5):
        for node_id, node in self.nodes.items():
            distances = []
            for other_id, other in self.nodes.items():
                if other_id != node_id:
                    dist = self._haversine(
                        node.lat, node.lon, other.lat, other.lon
                    )
                    distances.append((other_id, dist))

            distances.sort(key=lambda x: x[1])
            node.neighbors = [d[0] for d in distances[:max_neighbors]]

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))

    def simulate_cosmic_ray(self, particle: ParticleType = ParticleType.MUON,
                           affected_area_km2: float = 100.0) -> List[Event]:
        radius_km = math.sqrt(affected_area_km2 / math.pi)

        center_lat = random.uniform(-60, 60)
        center_lon = random.uniform(-180, 180)

        affected_nodes = []
        for node_id, node in self.nodes.items():
            dist = self._haversine(center_lat, center_lon, node.lat, node.lon)
            if dist <= radius_km:
                affected_nodes.append(node_id)

        n_affected = min(len(affected_nodes), random.randint(10, 100))
        affected_nodes = random.sample(affected_nodes, n_affected)

        events = []
        for node_id in affected_nodes:
            event = self.nodes[node_id].detect(particle)
            if event and event.confidence > 0.85:
                events.append(event)
                self._propagate_gossip(event)

        if len(events) >= 5:
            self.coincident_events.append(events)
            self.global_events.extend(events)

        return events

    def _propagate_gossip(self, event: Event, ttl: int = 3):
        visited = {event.node_id}
        queue = [(event.node_id, ttl)]

        while queue:
            current_id, current_ttl = queue.pop(0)
            if current_ttl <= 0:
                continue

            node = self.nodes[current_id]
            recipients = node.share_event(event, current_ttl)

            for rid in recipients:
                if rid not in visited:
                    visited.add(rid)
                    queue.append((rid, current_ttl - 1))

    def estimate_direction(self, events: List[Event]) -> Optional[Tuple[float, float, float]]:
        if len(events) < 3:
            return None

        events_sorted = sorted(events, key=lambda e: e.timestamp)

        first = events_sorted[0]
        last = events_sorted[-1]

        dx = last.location[1] - first.location[1]
        dy = last.location[0] - first.location[0]
        dz = 1.0

        norm = math.sqrt(dx**2 + dy**2 + dz**2)
        if norm > 0:
            return (dx/norm, dy/norm, dz/norm)
        return None

    def statistics(self) -> Dict:
        total_detected = sum(n.events_detected for n in self.nodes.values())
        total_shared = sum(n.events_shared for n in self.nodes.values())

        return {
            'n_nodes': self.n_nodes,
            'total_events_detected': total_detected,
            'total_events_shared': total_shared,
            'global_events': len(self.global_events),
            'coincident_showers': len(self.coincident_events),
            'avg_events_per_shower': (
                sum(len(e) for e in self.coincident_events) /
                len(self.coincident_events) if self.coincident_events else 0
            ),
            'network_coverage_km2': self._estimate_coverage(),
            'phi_c': self._compute_phi_c()
        }

    def _estimate_coverage(self) -> float:
        wifi_nodes = sum(1 for n in self.nodes.values()
                        if n.sensors['wifi'].efficiency > 0)
        coverage_per_node = math.pi * (10**2)
        return wifi_nodes * coverage_per_node / 1e6

    def _compute_phi_c(self) -> float:
        if not self.global_events:
            return 0.0

        valid = sum(1 for e in self.global_events
                     if e.particle_type != ParticleType.NOISE)
        return valid / len(self.global_events)
