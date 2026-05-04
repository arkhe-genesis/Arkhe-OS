#!/usr/bin/env python3
"""
Sacred Polyhedra Framework — Extension of Substrate 90 to Tetrahedron, Cuboctahedron, Icosahedron
Each polyhedron defines a cavity geometry with N coherent waves along symmetry axes.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class SacredPolyhedronParams(ABC):
    """Abstract base for sacred polyhedron cavity parameters."""
    radius: float = 1.0  # Circumradius
    depth: float = 0.5   # Parabolic depth factor
    base_frequency: float = 2.0
    coupling_strength: float = 0.1

    @abstractmethod
    def n_waves(self) -> int:
        """Number of coherent wave modes (symmetry axes)."""
        pass

    @abstractmethod
    def wave_directions(self) -> np.ndarray:
        """Unit vectors along symmetry axes for wave propagation."""
        pass

    @abstractmethod
    def cavity_sdf(self, p: np.ndarray) -> float:
        """Signed distance function for the polyhedral parabolic cavity."""
        pass

class TetrahedronParams(SacredPolyhedronParams):
    """Tetrahedral cavity: 4 waves, 3-fold symmetry."""

    def n_waves(self) -> int:
        return 4

    def wave_directions(self) -> np.ndarray:
        # Tetrahedron vertices on unit sphere
        return np.array([
            [1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0],
        ], dtype=np.float32) / np.sqrt(3.0)

    def cavity_sdf(self, p: np.ndarray) -> float:
        # Tetrahedron SDF + parabolic vertical profile
        # Simplified: use distance to 4 planes defining tetrahedron
        planes = self._tetrahedron_planes()
        plane_dists = np.array([np.dot(p, n) - d for n, d in planes])
        tetra_d = np.max(plane_dists)  # Outside if any plane distance > 0

        # Parabolic profile in radial direction
        r = np.linalg.norm(p[:2])
        z_max = self.depth * (r / self.radius)**2 if r < self.radius else self.depth
        z_d = max(p[2] - z_max, -p[2])

        return max(tetra_d, z_d)

    def _tetrahedron_planes(self) -> List[Tuple[np.ndarray, float]]:
        """Return (normal, offset) for 4 tetrahedron faces."""
        # Precomputed for unit circumradius tetrahedron
        return [
            (np.array([1.0, 1.0, 1.0]) / np.sqrt(3), 1/np.sqrt(3)),
            (np.array([1.0, -1.0, -1.0]) / np.sqrt(3), 1/np.sqrt(3)),
            (np.array([-1.0, 1.0, -1.0]) / np.sqrt(3), 1/np.sqrt(3)),
            (np.array([-1.0, -1.0, 1.0]) / np.sqrt(3), 1/np.sqrt(3)),
        ]

class CuboctahedronParams(SacredPolyhedronParams):
    """Cuboctahedral cavity: 12 waves, 4-fold + 3-fold symmetry."""

    def n_waves(self) -> int:
        return 12

    def wave_directions(self) -> np.ndarray:
        # Cuboctahedron: vertices at permutations of (±1,±1,0) normalized
        dirs = []
        for signs in [(1,1,0), (1,-1,0), (-1,1,0), (-1,-1,0),
                      (1,0,1), (1,0,-1), (-1,0,1), (-1,0,-1),
                      (0,1,1), (0,1,-1), (0,-1,1), (0,-1,-1)]:
            v = np.array(signs, dtype=np.float32)
            dirs.append(v / np.linalg.norm(v))
        return np.array(dirs)

    def cavity_sdf(self, p: np.ndarray) -> float:
        # Cuboctahedron SDF via intersection of cube and octahedron
        # Simplified approximation
        cube_d = np.max(np.abs(p)) - self.radius / np.sqrt(2)
        octa_d = (np.sum(np.abs(p)) - self.radius * np.sqrt(3)) / np.sqrt(3)
        poly_d = max(cube_d, octa_d)

        # Parabolic profile
        r = np.linalg.norm(p[:2])
        z_max = self.depth * (r / self.radius)**2 if r < self.radius else self.depth
        z_d = max(p[2] - z_max, -p[2])

        return max(poly_d, z_d)

class IcosahedronParams(SacredPolyhedronParams):
    """Icosahedral cavity: 20 waves, 5-fold symmetry (golden ratio)."""

    def n_waves(self) -> int:
        return 20

    def wave_directions(self) -> np.ndarray:
        # Icosahedron vertices using golden ratio φ
        phi = (1.0 + np.sqrt(5.0)) / 2.0
        dirs = []
        # Cyclic permutations of (0, ±1, ±φ)
        for cyclic in [(0, 1, phi), (1, phi, 0), (phi, 0, 1)]:
            for signs in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                v = np.array([cyclic[0], cyclic[1]*signs[0], cyclic[2]*signs[1]], dtype=np.float32)
                dirs.append(v / np.linalg.norm(v))
        return np.array(dirs)

    def cavity_sdf(self, p: np.ndarray) -> float:
        # Icosahedron SDF approximation via 20 plane distances
        planes = self._icosahedron_planes()
        plane_dists = np.array([np.dot(p, n) - d for n, d in planes])
        icosa_d = np.max(plane_dists)

        # Parabolic profile
        r = np.linalg.norm(p[:2])
        z_max = self.depth * (r / self.radius)**2 if r < self.radius else self.depth
        z_d = max(p[2] - z_max, -p[2])

        return max(icosa_d, z_d)

    def _icosahedron_planes(self) -> List[Tuple[np.ndarray, float]]:
        """Return (normal, offset) for 20 icosahedron faces."""
        # Precomputed normals and offsets for unit circumradius icosahedron
        # Simplified: use vertex directions as approximate face normals
        phi = (1.0 + np.sqrt(5.0)) / 2.0
        planes = []
        for cyclic in [(0, 1, phi), (1, phi, 0), (phi, 0, 1)]:
            for signs in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                n = np.array([cyclic[0], cyclic[1]*signs[0], cyclic[2]*signs[1]], dtype=np.float32)
                n = n / np.linalg.norm(n)
                d = 0.5  # Approximate offset
                planes.append((n, d))
        return planes

# Factory function to create polyhedron params by name
def create_polyhedron(name: str, **kwargs) -> SacredPolyhedronParams:
    """Factory for sacred polyhedron parameters."""
    polyhedra = {
        'tetrahedron': TetrahedronParams,
        'cuboctahedron': CuboctahedronParams,
        'icosahedron': IcosahedronParams,
        'hexagon': lambda **kw: type('HexagonParams', (SacredPolyhedronParams,), {
            'n_waves': lambda self: 6,
            'wave_directions': lambda self: np.array([
                [1,0,0], [0.5,np.sqrt(3)/2,0], [-0.5,np.sqrt(3)/2,0],
                [-1,0,0], [-0.5,-np.sqrt(3)/2,0], [0.5,-np.sqrt(3)/2,0]
            ], dtype=np.float32),
            'cavity_sdf': lambda self, p: None  # Delegate to existing hex_distance
        })(**kwargs)
    }
    if name not in polyhedra:
        raise ValueError(f"Unknown polyhedron: {name}. Available: {list(polyhedra.keys())}")
    return polyhedra[name](**kwargs)
