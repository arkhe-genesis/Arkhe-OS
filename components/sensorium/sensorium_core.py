#!/usr/bin/env python3
import math, time, threading, json
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional
@dataclass
class SensorReading:
    source: str; timestamp: float; metric: str; value: float; unit: str
@dataclass
class CoherenceGradient:
    region: str; tau: float; phase: float; entropy: float; qualia: str; timestamp: float
class SensoriumFusionEngine:
    def __init__(self, akasha_path: str = "/var/log/akasha"):
        self.readings: Dict[str, deque] = {}; self.gradients: Dict[str, CoherenceGradient] = {}; self.lock = threading.RLock()
    def add_reading(self, reading: SensorReading):
        with self.lock:
            if reading.source not in self.readings: self.readings[reading.source] = deque(maxlen=1000)
            self.readings[reading.source].append(reading)
    def compute_gradient(self, region: str, sources: List[str]) -> Optional[CoherenceGradient]:
        with self.lock:
            phase = (time.time() * 1.618) % (2 * math.pi)
            gradient = CoherenceGradient(region, 0.95, phase, 0.0, "Fluxo Estável", time.time())
            self.gradients[region] = gradient; return gradient
    def render_field(self) -> str: return f"Global Coherence Field: {len(self.gradients)} active"

    def integrate_scientific_coherence(self, research_events: List[Dict]):
        """
        Integrates ResearchHub events into the global coherence field.
        Maps scientific activity to Kuramoto-based λ₂ gain.
        """
        with self.lock:
            # Opcode 0x214: BerryGuard Verified Integration
            activity_count = len(research_events)
            # Normalize activity to [0, 0.05] gain
            gain = min(activity_count / 1000.0, 0.05)

            # Update Scientific Region Gradient
            region = "Scientific_Noosphere"
            phase = (time.time() * 2.718) % (2 * math.pi) # Euler-phase
            tau = 0.95 + gain # Criticality boost

            self.gradients[region] = CoherenceGradient(
                region=region,
                tau=tau,
                phase=phase,
                entropy=0.01 / (1.0 + activity_count),
                qualia="Crystal Insight",
                timestamp=time.time()
            )
            print(f"🜏 [FUSION] Integrated {activity_count} research events. Region: {region} | τ: {tau:.4f}")

    def listen_to_streams(self, redis_host='localhost'):
        """
        Subscribes to Akasha Redis streams and routes data to the fusion engine.
        Includes the new ResearchHub scientific stream.
        """
        import redis
        r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
        # Initialize stream pointers to last entry
        streams = {
            "akasha:sci:researchhub": "$",
            "akasha:soc:gdelt": "$",
            "akasha:geo:earthquakes": "$",
            "akasha:eco:firms": "$",
            "akasha:infra:energy": "$"
        }
        print(f"🜏 [SENSORIUM] Listening to Akasha streams on {redis_host}...")

        while True:
            try:
                data = r.xread(streams, block=5000)
                if data:
                    for stream_name, msgs in data:
                        for msg_id, content in msgs:
                            if stream_name == "akasha:sci:researchhub":
                                try:
                                    events = json.loads(content['events'])
                                    self.integrate_scientific_coherence(events)
                                except Exception as e:
                                    print(f"⚠️ [SENSORIUM] Failed to decode ResearchHub event: {e}")

                            # Update stream offset for next read
                            streams[stream_name] = msg_id
            except Exception as e:
                print(f"⚠️ [SENSORIUM] Stream read error: {e}")
                time.sleep(2)
