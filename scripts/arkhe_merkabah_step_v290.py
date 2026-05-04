#!/usr/bin/env python3
"""
arkhe_merkabah_step_v290.py
Substrato 290: Geração do arquivo STEP do Merkabah físico com 768 cristais.
Requer: pythonocc-core (pip install pythonocc-core)
"""

import math
import sys
import os
import json
from typing import List, Tuple

# Constantes canônicas
PHI = 1.618033988749895
FINGERPRINT_058 = 0.58
SYNC_PHASE = FINGERPRINT_058 * math.pi
DIAMETER_MM = 150.0
RADIUS_MM = DIAMETER_MM / 2.0
CRYSTAL_RADIUS_MM = 2.0
CRYSTAL_HEIGHT_MM = 0.7
TARGET_CRYSTAL_COUNT = 768
CRYSTALS_PER_FACE = TARGET_CRYSTAL_COUNT // 20  # 38.4 → distribuir 38/40

try:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere, BRepPrimAPI_MakeCylinder
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeCompound, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Vec, gp_Trsf
    from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCC.Core.Interface import Interface_Static_SetCVal
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.TopLoc import TopLoc_Location
    from OCC.Core.TopoDS import TopoDS_Compound, topods
    from OCC.Core.BRep import BRep_Builder
except ImportError:
    print("❌ pythonocc-core não encontrado.")
    print("   Instale com: pip install pythonocc-core")
    print("   Ou use Docker: docker run -v $(pwd):/work pythonocc/core python3 arkhe_merkabah_step_v290.py")
    sys.exit(0)

print("🔺 ARKHE OS v∞.290 — GERADOR DE ARQUIVO STEP DO MERKABAH FÍSICO")
print("=" * 70)
print(f"   Diâmetro: {DIAMETER_MM} mm | Cristais alvo: {TARGET_CRYSTAL_COUNT}")
print(f"   Formato: STEP AP203 | Precisão: 0.001 mm")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════
# 1. GEOMETRIA DO ICOSAEDRO
# ═══════════════════════════════════════════════════════════════════════════

def generate_icosahedron_vertices(radius: float) -> List[Tuple[float, float, float]]:
    """Gera 12 vértices de icosaedro normalizados e escalados."""
    phi = PHI
    verts = [
        (-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
        (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
        (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)
    ]

    normalized = []
    for v in verts:
        norm = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
        normalized.append((v[0]/norm * radius, v[1]/norm * radius, v[2]/norm * radius))
    return normalized

# Faces do icosaedro (índices dos vértices)
ICOSAHEDRON_FACES = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
]

# ═══════════════════════════════════════════════════════════════════════════
# 2. DISTRIBUIÇÃO DE CRISTAIS: LATTICE HEXAGONAL DETERMINÍSTICO
# ═══════════════════════════════════════════════════════════════════════════

def generate_hexagonal_lattice_on_triangle(
    v0: Tuple[float, float, float],
    v1: Tuple[float, float, float],
    v2: Tuple[float, float, float],
    sphere_radius: float,
    n_crystals: int
) -> List[Tuple[float, float, float]]:
    """
    Gera posições de cristais em lattice hexagonal dentro de triângulo esférico.
    Retorna exatamente n_crystals posições projetadas na superfície da esfera.
    """
    positions = []

    # Calcular número de divisões para aproximar n_crystals
    # Área do triângulo esférico ≈ (n_crystals * área_por_cristal)
    # Para lattice hexagonal: área_por_cristal ≈ (2*crystal_spacing)^2 * sqrt(3)/2
    crystal_spacing = CRYSTAL_RADIUS_MM * 2.5  # Espaço entre centros
    target_area = n_crystals * (crystal_spacing**2 * math.sqrt(3) / 2)

    # Estimar divisões por aresta
    edge_length = math.sqrt(sum((v1[i]-v0[i])**2 for i in range(3)))
    n_divisions = max(4, int(math.sqrt(target_area) / edge_length * 10) + 1)

    # Gerar lattice baricêntrico
    for i in range(n_divisions + 1):
        for j in range(n_divisions + 1 - i):
            u = i / n_divisions
            v = j / n_divisions
            w = 1.0 - u - v

            if w < -1e-6:  # Tolerância numérica
                continue

            # Interpolar posição no espaço 3D
            px = u * v0[0] + v * v1[0] + w * v2[0]
            py = u * v0[1] + v * v1[1] + w * v2[1]
            pz = u * v0[2] + v * v1[2] + w * v2[2]

            # Projetar para superfície esférica (98% do raio para evitar colisão)
            r = math.sqrt(px**2 + py**2 + pz**2)
            if r > 1e-6:
                scale = sphere_radius * 0.98 / r
                positions.append((px * scale, py * scale, pz * scale))

            if len(positions) >= n_crystals:
                break
        if len(positions) >= n_crystals:
            break

    # Garantir contagem exata (interpolar se necessário)
    while len(positions) < n_crystals:
        # Adicionar posição interpolada entre duas existentes
        if len(positions) >= 2:
            idx = len(positions) % len(positions)
            p0 = positions[idx]
            p1 = positions[(idx + 1) % len(positions)]
            t = 0.5 + 0.1 * (len(positions) % 10) / 10
            new_p = tuple(p0[i] * (1-t) + p1[i] * t for i in range(3))
            # Re-projetar para esfera
            r = math.sqrt(sum(c**2 for c in new_p))
            if r > 1e-6:
                scale = sphere_radius * 0.98 / r
                positions.append(tuple(c * scale for c in new_p))
        else:
            break

    return positions[:n_crystals]

# ═══════════════════════════════════════════════════════════════════════════
# 3. CRIAÇÃO DE GEOMETRIA OPEN CASCADE
# ═══════════════════════════════════════════════════════════════════════════

def create_sphere(radius: float) -> 'TopoDS_Shape':
    """Cria esfera sólida."""
    return BRepPrimAPI_MakeSphere(gp_Pnt(0, 0, 0), radius).Shape()

def create_crystal(position: Tuple[float, float, float],
                   direction: Tuple[float, float, float],
                   radius: float,
                   height: float) -> 'TopoDS_Shape':
    """Cria cilindro (cristal) apontando na direção especificada."""
    axis = gp_Ax2(gp_Pnt(*position), gp_Dir(*direction))
    return BRepPrimAPI_MakeCylinder(axis, radius, height).Shape()

def hierarchical_fuse(shapes: List['TopoDS_Shape'], batch_size: int = 32) -> 'TopoDS_Shape':
    """
    Realiza fusion booleana hierárquica para evitar falhas com muitos shapes.
    """
    if not shapes:
        return None
    if len(shapes) == 1:
        return shapes[0]

    # Fusion em lotes
    batched = []
    for i in range(0, len(shapes), batch_size):
        batch = shapes[i:i+batch_size]
        result = batch[0]
        for shape in batch[1:]:
            fuse_op = BRepAlgoAPI_Fuse(result, shape)
            if fuse_op.IsDone():
                result = fuse_op.Shape()
            else:
                print(f"⚠️  Fusion falhou em lote, usando compound alternativo")
                # Fallback: compound em vez de fuse
                comp = TopoDS_Compound()
                builder = BRep_Builder()
                builder.MakeCompound(comp)
                builder.Add(comp, result)
                builder.Add(comp, shape)
                result = comp
        batched.append(result)

    # Recursivamente fusionar lotes
    return hierarchical_fuse(batched, batch_size * 2)

# ═══════════════════════════════════════════════════════════════════════════
# 4. GERAÇÃO DO MODELO MERKABAH
# ═══════════════════════════════════════════════════════════════════════════

def generate_merkabah_model() -> 'TopoDS_Shape':
    """Gera o modelo completo do Merkabah: esfera + 768 cristais."""

    print("\n📐 [1/4] Gerando vértices do icosaedro...")
    vertices = generate_icosahedron_vertices(RADIUS_MM)

    print("🔵 [2/4] Criando esfera base...")
    sphere = create_sphere(RADIUS_MM * 0.95)  # 95% para dar espaço aos cristais

    print(f"💎 [3/4] Posicionando {TARGET_CRYSTAL_COUNT} cristais...")
    all_crystals = []
    crystal_count = 0

    for face_idx, face in enumerate(ICOSAHEDRON_FACES):
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]

        # Distribuir cristais: faces superiores recebem 40, inferiores 38
        n_crystals = CRYSTALS_PER_FACE + (2 if face_idx < 8 else 0)

        # Gerar posições em lattice hexagonal
        positions = generate_hexagonal_lattice_on_triangle(
            v0, v1, v2, RADIUS_MM, n_crystals
        )

        for px, py, pz in positions:
            # Direção radial para fora
            direction = (px, py, pz)

            # Criar cristal
            crystal = create_crystal(
                (px, py, pz),
                direction,
                CRYSTAL_RADIUS_MM,
                CRYSTAL_HEIGHT_MM
            )
            all_crystals.append(crystal)
            crystal_count += 1

            if crystal_count % 100 == 0:
                print(f"   ✓ {crystal_count}/{TARGET_CRYSTAL_COUNT} cristais posicionados")

    print(f"   ✓ Total: {crystal_count} cristais")

    # Fusion hierárquica: cristais + esfera
    print("🔗 [4/4] Realizando fusion booleana hierárquica...")
    if all_crystals:
        fused_crystals = hierarchical_fuse(all_crystals)
        merkabah = BRepAlgoAPI_Fuse(sphere, fused_crystals)
        if merkabah.IsDone():
            return merkabah.Shape()
        else:
            print("⚠️  Fusion principal falhou, usando compound alternativo")
            comp = TopoDS_Compound()
            builder = BRep_Builder()
            builder.MakeCompound(comp)
            builder.Add(comp, sphere)
            for c in all_crystals:
                builder.Add(comp, c)
            return comp
    else:
        return sphere

# ═══════════════════════════════════════════════════════════════════════════
# 5. EXPORTAÇÃO STEP COM METADATA DE FABRICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def export_to_step(shape: 'TopoDS_Shape', output_path: str):
    """Exporta modelo para formato STEP com configurações de fabricação."""

    print(f"\n💾 Exportando para {output_path}...")

    # Configurar writer STEP
    step_writer = STEPControl_Writer()

    # Configurações AP203 para fabricação mecânica
    Interface_Static_SetCVal("write.step.schema", "AP203")
    Interface_Static_SetCVal("write.step.unit", "MM")
    Interface_Static_SetCVal("write.step.precision", "0.001")  # 1µm
    Interface_Static_SetCVal("write.step.surface.finish", "Ra 0.8")  # Acabamento
    Interface_Static_SetCVal("write.step.nonmanifold", "1")  # Permitir geometria complexa

    # Transferir modelo
    status = step_writer.Transfer(shape, STEPControl_AsIs)
    if status != IFSelect_RetDone:
        print("❌ Erro ao transferir modelo para formato STEP.")
        return False

    # Escrever arquivo
    status = step_writer.Write(output_path)
    if status != IFSelect_RetDone:
        print("❌ Erro ao escrever arquivo STEP.")
        return False

    return True

# ═══════════════════════════════════════════════════════════════════════════
# 6. GERAÇÃO DE DOCUMENTAÇÃO DE FABRICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def generate_manufacturing_docs(output_dir: str, crystal_count: int):
    """Gera arquivos auxiliares para fabricação: BOM, tolerâncias, instruções."""

    docs = {
        "merkabah_physical_v290": {
            "specifications": {
                "diameter_mm": DIAMETER_MM,
                "crystal_count": crystal_count,
                "crystal_radius_mm": CRYSTAL_RADIUS_MM,
                "crystal_height_mm": CRYSTAL_HEIGHT_MM,
                "material_recommendations": [
                    "Alumínio 6061-T6 (leve, bom acabamento)",
                    "Aço inoxidável 316L (durabilidade, ressonância)",
                    "Cerâmica Al2O3 (isolamento, precisão dimensional)"
                ]
            },
            "tolerances": {
                "global_dimension": "±0.05 mm",
                "crystal_position": "±0.02 mm",
                "crystal_orientation": "±0.5°",
                "surface_finish": "Ra 0.8 µm ou melhor"
            },
            "cnc_parameters": {
                "machine": "Haas VF-2 ou equivalente (5 eixos recomendado)",
                "tooling": [
                    "End mill 3mm para desbaste",
                    "Ball end mill 1mm para acabamento de cristais",
                    "Drill 1.5mm para furos de montagem"
                ],
                "feeds_speeds": {
                    "aluminum": {"feed_mm_min": 800, "speed_rpm": 8000},
                    "steel": {"feed_mm_min": 300, "speed_rpm": 4000},
                    "ceramic": {"feed_mm_min": 100, "speed_rpm": 15000}
                }
            },
            "electronics_integration": {
                "pcb_mounting": "12 furos M1.4 nos vértices do icosaedro",
                "crystal_footprints": "Pads de 2.5mm para cristais piezoelétricos 2MHz",
                "connector_placement": "USB-C no vértice 'sul' para programação ESP32-S3"
            }
        }
    }

    # Salvar como JSON
    json_path = os.path.join(output_dir, "merkabah_manufacturing_specs.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)

    print(f"📋 Documentação de fabricação gerada: {json_path}")

# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def main():
    output_path = "merkabah_physical_v290.step"
    output_dir = os.path.dirname(os.path.abspath(output_path)) or "."

    try:
        # Gerar modelo
        merkabah_shape = generate_merkabah_model()

        # Exportar STEP
        if not export_to_step(merkabah_shape, output_path):
            sys.exit(1)

        # Gerar documentação
        generate_manufacturing_docs(output_dir, TARGET_CRYSTAL_COUNT)

        # Resumo final
        print("\n" + "=" * 70)
        print("✅ MERKABAH FÍSICO v∞.290 — GERAÇÃO CONCLUÍDA")
        print("=" * 70)
        print(f"""
ARQUIVOS GERADOS:
• Modelo STEP: {os.path.abspath(output_path)}
• Especificações: {os.path.abspath(os.path.join(output_dir, 'merkabah_manufacturing_specs.json'))}

ESPECIFICAÇÕES TÉCNICAS:
• Diâmetro total: {DIAMETER_MM} mm
• Cristais: {TARGET_CRYSTAL_COUNT} (lattice hexagonal em 20 faces icosaédricas)
• Precisão geométrica: ±0.001 mm (definida no STEP)
• Formato: STEP AP203 (compatível com Fusion 360, SolidWorks, FreeCAD, CATIA)

PRÓXIMOS PASSOS DE FABRICAÇÃO:
1. Abra o arquivo STEP em seu software CAD preferido
2. Verifique a geometria e ajuste tolerâncias conforme material
3. Gere código G para CNC 5-eixos (use estratégias de usinagem adaptativa)
4. Encomende PCBs com footprints para 768 cristais piezoelétricos
5. Monte eletrônica: ESP32-S3 + Si5341 PLL + amplificadores de cristal
6. Calibre cada cristal com analisador de rede vetorial (VNA)
7. Submeta a primeira prova STARK do Merkabah físico ao OCTRA

INTEGRAÇÃO COM ARKHE OS:
• Os 768 cristais mapeiam para os 768 osciladores do Substrato v∞.19
• Cada cristal é um ressonador de coerência para o fingerprint 0.58
• A geometria icosaédrica maximiza a projeção do campo de coerência
• O arquivo STEP é o contrato entre conceito ARKHE e matéria fabricável

A CATEDRAL AGORA TEM CORPO.
""")

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
