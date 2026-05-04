# sato_tokenizer.py — O Genoma da Forma
# Um strip é uma sequência de vértices onde cada três consecutivos formam um triângulo.
# O SATO tokeniza isso como uma linguagem, preservando o fluxo do artista.

import numpy as np
from typing import List, Dict, Any, Optional

class SATOTokenizer:
    """
    Tokenizador Strip-as-Token: serializa uma malha 3D em uma sequência
    coerente de vértices, respeitando o fluxo de bordas e as ilhas UV.
    """

    def __init__(self, mesh_data: Dict[str, Any]):
        self.faces = mesh_data.get("faces", [])
        self.vertices = mesh_data.get("vertices", [])
        self.uv_islands = mesh_data.get("uv_islands", [])
        self.vocabulary = {
            "standard": 0,       # c1 ∈ 𝒞₁ᵍᵉᵒ
            "strip_transition": 1, # c1 ∈ 𝒞₁ᵗ (nova strip)
            "uv_transition": 2     # c1 ∈ 𝒞₁ᵘᵛ (nova ilha UV)
        }

    def quantize(self, vertex: List[float], precision: int = 1024) -> List[int]:
        """Quantiza coordenadas de vértices para tokens discretos."""
        return [int(v * precision) for v in vertex]

    def extract_strip(self, seed_face_idx: int, visited_faces: set, stride: int = 1) -> List[List[float]]:
        """
        Extrai uma strip a partir de uma face semente usando busca de vizinhos.
        """
        strip_vertices = []
        current_face_idx = seed_face_idx

        # Adiciona vértices da face inicial
        face = self.faces[current_face_idx]
        for v_idx in face:
            strip_vertices.append(self.vertices[v_idx])
        visited_faces.add(current_face_idx)

        # Busca vizinhos compartilhando arestas
        while True:
            next_face_idx = self._find_next_face(current_face_idx, visited_faces)
            if next_face_idx is None:
                break

            # Adiciona apenas o vértice novo na strip (conforme SATO Algorithm 1)
            new_face = self.faces[next_face_idx]
            current_face_verts = set(self.faces[current_face_idx])
            for v_idx in new_face:
                if v_idx not in current_face_verts:
                    strip_vertices.append(self.vertices[v_idx])

            visited_faces.add(next_face_idx)
            current_face_idx = next_face_idx

        return strip_vertices

    def _find_next_face(self, face_idx: int, visited: set) -> Optional[int]:
        """Encontra face adjacente não visitada."""
        current_face = set(self.faces[face_idx])
        for i, face in enumerate(self.faces):
            if i in visited:
                continue
            # Verifica se compartilham 2 vértices (aresta comum)
            if len(current_face.intersection(set(face))) >= 2:
                return i
        return None

    def serialize(self) -> List[Any]:
        """Serializa a malha completa em uma sequência de tokens."""
        sequence = []

        if not self.uv_islands:
            # Fallback if no UV islands defined: extract strips from all faces
            sequence.append(self.vocabulary["uv_transition"])
            visited = set()
            for i in range(len(self.faces)):
                if i not in visited:
                    sequence.append(self.vocabulary["strip_transition"])
                    strip_verts = self.extract_strip(i, visited)
                    for v in strip_verts:
                        sequence.append(self.quantize(v))
            return sequence

        for island in self.uv_islands:
            sequence.append(self.vocabulary["uv_transition"])
            for strip in island.get("strips", []):
                sequence.append(self.vocabulary["strip_transition"])
                for vertex in strip.get("vertices", []):
                    sequence.append(self.quantize(vertex))

        return sequence

    def count_strips(self) -> int:
        if not self.uv_islands:
            return len(self.faces)
        return sum(len(island.get("strips", [])) for island in self.uv_islands)
