#!/usr/bin/env python3
"""
562-BIS-CRUMBLE-VIS  –  ARKHE OS Integration Bridge
Substrate: 562-STIM-QEC-SIMULATOR → 485-HOLOGRAPHIC-PROJECTOR v2.0

Converts Stim circuits into Crumble interactive editor format and projects
stabilizer dynamics as holographic visualizations. Enables real-time,
interactive exploration of QEC braids, anyon trajectories, and detector
error models in the Cathedral's holographic display environment.

Dependencies: stim, json, numpy
License: Apache-2.0
Author: ARKHE OS Architect (ORCID 0009-0005-2697-4668)
"""

from __future__ import annotations
import json
import math
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np

try:
    import stim
except ImportError:
    raise RuntimeError(
        "stim required. Install:  pip install stim  "
        "(see https://github.com/quantumlib/Stim)"
    )


# ───────────────────────────────────────────────────────────────────────────────
# §1  Data Structures for Holographic Projection
# ───────────────────────────────────────────────────────────────────────────────

@dataclass
class HolographicQubit:
    """A single qubit rendered in the 485-HOLOGRAPHIC-PROJECTOR voxel space."""
    qubit_id: int
    x: float
    y: float
    z: float
    role: str          # "data", "ancilla_x", "ancilla_z", "magic_state"
    color_hex: str     # ARGB hex for holographic emission
    glow_intensity: float  # 0.0–1.0, mapped to projector lumen output

    def to_crumble_dict(self) -> Dict[str, Any]:
        return {
            "id": self.qubit_id,
            "position": [self.x, self.y, self.z],
            "role": self.role,
            "style": {
                "color": self.color_hex,
                "glow": self.glow_intensity,
                "radius": 0.15 if self.role == "data" else 0.10,
            },
        }


@dataclass
class HolographicGate:
    """A gate operation rendered as a light-beam or braid strand."""
    gate_type: str     # "H", "CNOT", "R", "M", "DEPOLARIZE", etc.
    targets: List[int]
    time_step: int
    color_hex: str
    beam_width: float  # visual thickness

    def to_crumble_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate_type,
            "targets": self.targets,
            "t": self.time_step,
            "style": {
                "color": self.color_hex,
                "width": self.beam_width,
                "dash": self.gate_type in ["DEPOLARIZE1", "DEPOLARIZE2", "X_ERROR"],
            },
        }


@dataclass
class HolographicDetector:
    """A detector (stabilizer measurement comparison) as a resonance node."""
    detector_id: int
    coords: Tuple[float, float, float]
    involved_qubits: List[int]
    is_active: bool    # True if detector fires (syndrome bit = 1)

    def to_crumble_dict(self) -> Dict[str, Any]:
        return {
            "id": self.detector_id,
            "position": list(self.coords),
            "involved": self.involved_qubits,
            "active": self.is_active,
            "style": {
                "color": "#FF0040" if self.is_active else "#00FF80",
                "pulse_freq": 2.0 if self.is_active else 0.5,
            },
        }


@dataclass
class CrumbleScene:
    """Complete scene descriptor for Crumble / 485-HOLOGRAPHIC-PROJECTOR."""
    scene_id: str
    substrate_source: str      # e.g., "562-STIM-QEC-SIMULATOR"
    qubits: List[HolographicQubit]
    gates: List[HolographicGate]
    detectors: List[HolographicDetector]
    camera_position: Tuple[float, float, float]
    camera_target: Tuple[float, float, float]

    def to_crumble_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


# ───────────────────────────────────────────────────────────────────────────────
# §2  Stim → Crumble Converter
# ───────────────────────────────────────────────────────────────────────────────

class StimToCrumbleConverter:
    """
    Converts a stim.Circuit into a Crumble-compatible holographic scene.

    The converter respects 485-HOLOGRAPHIC-PROJECTOR v2.0's coordinate system:
      • X-Y plane = physical chip layout
      • Z axis = time (circuit depth)
      • Color = gate type / noise channel
      • Glow intensity = error probability (for noise channels)
    """

    # Color palette aligned with 485-HOLOGRAPHIC-PROJECTOR v2.0 spectral calibration
    GATE_COLORS = {
        "R": "#00FFFF",           # Cyan: reset
        "H": "#FF00FF",           # Magenta: Hadamard
        "CNOT": "#FFFF00",        # Yellow: entanglement
        "M": "#FFFFFF",           # White: measurement
        "X_ERROR": "#FF0000",     # Red: Pauli-X noise
        "Z_ERROR": "#0000FF",     # Blue: Pauli-Z noise
        "DEPOLARIZE1": "#FF8000", # Orange: single-qubit depolarization
        "DEPOLARIZE2": "#FF4000", # Deep orange: two-qubit depolarization
        "SHIFT_COORDS": "#808080",# Gray: coordinate shift
        "QUBIT_COORDS": "#404040",# Dark gray: coordinate annotation
        "OBSERVABLE_INCLUDE": "#00FF00", # Green: logical observable
    }

    def __init__(self, z_scale: float = 0.5):
        """
        Parameters
        ----------
        z_scale : float
            Vertical scaling factor for time axis (Z = time_step * z_scale).
        """
        self.z_scale = z_scale
        self.qubit_coords_2d: Dict[int, Tuple[float, float]] = {}
        self.qubit_roles: Dict[int, str] = {}

    def convert_circuit(self, circuit: stim.Circuit, scene_id: str) -> CrumbleScene:
        """
        Main entry point: parse a stim.Circuit and emit a CrumbleScene.

        Parameters
        ----------
        circuit : stim.Circuit
            The circuit to visualize.
        scene_id : str
            Unique identifier for this scene.

        Returns
        -------
        CrumbleScene
        """
        qubits: List[HolographicQubit] = []
        gates: List[HolographicGate] = []
        detectors: List[HolographicDetector] = []

        # First pass: extract QUBIT_COORDS annotations
        self._extract_coordinates(circuit)

        # Build qubit objects
        for qid, (x, y) in self.qubit_coords_2d.items():
            role = self.qubit_roles.get(qid, "data")
            color = self._role_color(role)
            qubits.append(HolographicQubit(
                qubit_id=qid,
                x=x,
                y=y,
                z=0.0,  # initial time layer
                role=role,
                color_hex=color,
                glow_intensity=0.3,
            ))

        # Second pass: iterate operations and build gates
        time_step = 0
        for op in circuit.flattened():
            gate_type = op.name
            targets = list(op.targets_copy())
            args = list(op.gate_args_copy())

            if gate_type == "QUBIT_COORDS":
                continue  # already handled

            if gate_type == "SHIFT_COORDS" or gate_type == "TICK":
                if gate_type == "TICK":
                    time_step += 1
                continue

            color = self.GATE_COLORS.get(gate_type, "#AAAAAA")

            # Noise gates get thicker beams proportional to error rate
            beam_width = 0.02
            if "ERROR" in gate_type or "DEPOLARIZE" in gate_type:
                # Extract probability from gate args if available
                p_val = 0.0
                if len(args) > 0:
                    p_val = args[0]
                beam_width = 0.02 + p_val * 0.20  # max 0.22 for p=1.0

            clean_targets = []
            for t in targets:
                if t.is_qubit_target:
                    clean_targets.append(t.value)

            if not clean_targets:
                continue

            gates.append(HolographicGate(
                gate_type=gate_type,
                targets=clean_targets,
                time_step=time_step,
                color_hex=color,
                beam_width=beam_width,
            ))

            # Update qubit Z positions to track through time
            for t in clean_targets:
                qid = t
                # If generated circuit has more qubits than we annotated, skip update
                qubit_obj = next((q for q in qubits if q.qubit_id == qid), None)
                if qubit_obj:
                    qubit_obj.z = time_step * self.z_scale

        # Detectors: derived from DEM (simplified)
        # In a full implementation, we would parse the DEM and map detectors
        # to their spatial median coordinates.
        dem = circuit.detector_error_model()
        for det_idx in range(min(dem.num_detectors, 50)):  # cap for performance
            # Placeholder: detectors at lattice center with slight jitter
            cx = sum(q.x for q in qubits) / max(len(qubits), 1)
            cy = sum(q.y for q in qubits) / max(len(qubits), 1)
            cz = time_step * self.z_scale / 2
            detectors.append(HolographicDetector(
                detector_id=det_idx,
                coords=(cx + (det_idx % 5) * 0.1, cy + (det_idx // 5) * 0.1, cz),
                involved_qubits=[q.qubit_id for q in qubits[:4]],
                is_active=False,  # would be set from shot data
            ))

        # Camera: orbit around center of qubit cloud
        center_x = sum(q.x for q in qubits) / max(len(qubits), 1)
        center_y = sum(q.y for q in qubits) / max(len(qubits), 1)
        center_z = time_step * self.z_scale / 2

        return CrumbleScene(
            scene_id=scene_id,
            substrate_source="562-STIM-QEC-SIMULATOR",
            qubits=qubits,
            gates=gates,
            detectors=detectors,
            camera_position=(center_x + 5.0, center_y + 5.0, center_z + 3.0),
            camera_target=(center_x, center_y, center_z),
        )

    def _extract_coordinates(self, circuit: stim.Circuit) -> None:
        """Parse QUBIT_COORDS instructions to build 2D layout."""
        for op in circuit.flattened():
            if op.name == "QUBIT_COORDS":
                targets = list(op.targets_copy())
                args = list(op.gate_args_copy())
                if len(targets) >= 1 and len(args) >= 2:
                    qid = targets[0].value
                    x, y = args[0], args[1]
                    self.qubit_coords_2d[qid] = (x, y)
                    # Infer role from coordinate parity (ARKHE surface-code convention)
                    if (int(x) + int(y)) % 2 == 0:
                        self.qubit_roles[qid] = "data"
                    elif int(x) % 2 == 1:
                        self.qubit_roles[qid] = "ancilla_x"
                    else:
                        self.qubit_roles[qid] = "ancilla_z"

    def _role_color(self, role: str) -> str:
        return {
            "data": "#E0E0E0",
            "ancilla_x": "#FF6060",
            "ancilla_z": "#6060FF",
            "magic_state": "#FFD700",
        }.get(role, "#AAAAAA")

    # ──────────────────────────────────────────────────────────────────────────
    # §3  485-HOLOGRAPHIC-PROJECTOR v2.0 Native Format
    # ──────────────────────────────────────────────────────────────────────────
    def to_holographic_projector_stream(self, scene: CrumbleScene) -> Dict[str, Any]:
        """
        Convert CrumbleScene to 485-HOLOGRAPHIC-PROJECTOR v2.0 native stream format.

        The projector expects a time-ordered sequence of "frames" where each
        frame updates qubit states, active gates, and detector pulses.
        """
        frames = []
        max_t = max((g.time_step for g in scene.gates), default=0)

        for t in range(max_t + 1):
            frame_gates = [g for g in scene.gates if g.time_step == t]
            frame = {
                "frame_index": t,
                "timestamp_ms": t * 100,  # 100ms per time step
                "qubits": [
                    {
                        "id": q.qubit_id,
                        "position": [q.x, q.y, t * self.z_scale],
                        "state": "active" if any(q.qubit_id in g.targets for g in frame_gates) else "idle",
                        "style": asdict(q),
                    }
                    for q in scene.qubits
                ],
                "gates": [g.to_crumble_dict() for g in frame_gates],
                "detectors": [
                    d.to_crumble_dict()
                    for d in scene.detectors
                    if d.coords[2] <= t * self.z_scale
                ],
            }
            frames.append(frame)

        return {
            "format_version": "485-HOLOGRAPHIC-PROJECTOR-v2.0",
            "scene_id": scene.scene_id,
            "substrate": scene.substrate_source,
            "total_frames": len(frames),
            "fps_target": 10,
            "resolution_voxels": [1920, 1080, 720],  # X, Y, Z holographic resolution
            "color_space": "ARGB-8888",
            "frames": frames,
        }


# ───────────────────────────────────────────────────────────────────────────────
# §4  Anyon Trajectory Visualizer (557-ISING-BRAID integration)
# ───────────────────────────────────────────────────────────────────────────────

class AnyonTrajectoryRenderer:
    """
    Renders Majorana anyon braiding trajectories as 3D helical paths
    compatible with 485-HOLOGRAPHIC-PROJECTOR and 557-ISING-BRAID.

    Anyons move along Z(time) while orbiting their vortex core in XY.
    The braid intersection pattern encodes the unitary gate.
    """

    def __init__(self, radius: float = 1.0, pitch: float = 0.3):
        self.radius = radius
        self.pitch = pitch

    def render_braid(
        self,
        braid_sequence: List[Tuple[int, int, str]],  # (anyon_a, anyon_b, "over"/"under")
        num_anyons: int = 4,
        steps_per_exchange: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Generate a list of frame updates showing anyons braiding.

        Parameters
        ----------
        braid_sequence : list of (int, int, str)
            Each tuple is (anyon_index_a, anyon_index_b, crossing_type).
        num_anyons : int
            Number of anyons in the system.
        steps_per_exchange : int
            Temporal resolution for each exchange operation.

        Returns
        -------
        list of frame dicts
        """
        frames = []
        # Initial positions: evenly spaced on a circle
        angles = [2 * math.pi * i / num_anyons for i in range(num_anyons)]
        positions = {
            i: {"x": self.radius * math.cos(a), "y": self.radius * math.sin(a), "z": 0.0}
            for i, a in enumerate(angles)
        }

        global_time = 0
        for a_idx, b_idx, cross_type in braid_sequence:
            # Animate exchange between anyon a_idx and anyon b_idx
            pos_a = positions[a_idx]
            pos_b = positions[b_idx]

            for step in range(steps_per_exchange):
                t = step / steps_per_exchange
                # Circular exchange path
                mid_x = (pos_a["x"] + pos_b["x"]) / 2
                mid_y = (pos_a["y"] + pos_b["y"]) / 2

                # Orbit around midpoint
                orbit_angle = math.pi * t
                if cross_type == "over":
                    orbit_angle += 0.1  # slight vertical separation for over/under

                dx = pos_b["x"] - pos_a["x"]
                dy = pos_b["y"] - pos_a["y"]
                dist = math.hypot(dx, dy)

                new_a_x = mid_x + (dist/2) * math.cos(orbit_angle + math.pi)
                new_a_y = mid_y + (dist/2) * math.sin(orbit_angle + math.pi)
                new_b_x = mid_x + (dist/2) * math.cos(orbit_angle)
                new_b_y = mid_y + (dist/2) * math.sin(orbit_angle)

                z = global_time * self.pitch + step * (self.pitch / steps_per_exchange)

                frame = {
                    "frame_index": global_time * steps_per_exchange + step,
                    "anyon_positions": [
                        {
                            "id": i,
                            "x": new_a_x if i == a_idx else (new_b_x if i == b_idx else positions[i]["x"]),
                            "y": new_a_y if i == a_idx else (new_b_y if i == b_idx else positions[i]["y"]),
                            "z": z,
                            "color": "#FF0000" if i == a_idx else ("#0000FF" if i == b_idx else "#00FF00"),
                            "glow": 1.0 if i in (a_idx, b_idx) else 0.4,
                        }
                        for i in range(num_anyons)
                    ],
                    "braid_event": {
                        "type": cross_type,
                        "participants": [a_idx, b_idx],
                        "progress": t,
                    },
                }
                frames.append(frame)

            # Swap final positions
            positions[a_idx], positions[b_idx] = positions[b_idx], positions[a_idx]
            global_time += 1

        return frames


# ═══════════════════════════════════════════════════════════════════════════════
# CLI / Quick-test entry point
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 70)
    print("562-BIS-CRUMBLE-VIS  –  Holographic Projection Bridge")
    print("═" * 70)

    # ── Example 1: Surface code d=3 → Crumble scene ──
    print("\\n[1] Converting surface-code d=3 circuit to Crumble scene ...")
    from importlib import import_module
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    bridge_453 = import_module("562-BIS-453-QUANTUM_SurfaceCode_Stim_Bridge")
    builder = bridge_453.SurfaceCodeStimBridge(distance=3, rounds=3, physical_error_rate=0.001)
    circuit = builder.build_memory_experiment()

    converter = StimToCrumbleConverter(z_scale=0.5)
    scene = converter.convert_circuit(circuit, scene_id="453_d3_r3_demo")
    projector_stream = converter.to_holographic_projector_stream(scene)

    print(f"    Qubits: {len(scene.qubits)}  |  Gates: {len(scene.gates)}  |  Frames: {projector_stream['total_frames']}")

    # Save sample frame
    import tempfile
    with tempfile.NamedTemporaryFile(prefix="crumble_scene_d3_", suffix=".json", delete=False, mode="w") as f:
        json.dump(projector_stream, f, indent=2)
        print(f"    Saved projector stream to {f.name}")

    # ── Example 2: Anyon braid trajectory ──
    print("\\n[2] Rendering Ising anyon braid (557-ISING-BRAID) ...")
    renderer = AnyonTrajectoryRenderer(radius=2.0, pitch=0.5)
    braid_seq = [(0, 1, "over"), (1, 2, "under"), (2, 3, "over")]
    anyon_frames = renderer.render_braid(braid_seq, num_anyons=4, steps_per_exchange=24)
    print(f"    Braid frames: {len(anyon_frames)}  |  Anyons: 4  |  Exchanges: {len(braid_seq)}")

    print("\\n[✓] Visualization bridge operational. Ready for 485-HOLOGRAPHIC-PROJECTOR v2.0.")
    print("═" * 70)
