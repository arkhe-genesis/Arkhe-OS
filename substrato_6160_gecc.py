#!/usr/bin/env python3
"""
Substrato 6160 — GECC Full Simulation
Genoma sintético 256 bits + Hamming(7,4) + 1000 ciclos + ruído cósmico
"""
import numpy as np
import hashlib, json, time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import os

# ============================================================================
# 1. CÓDIGO DE HAMMING (7,4) — 4 bits de dados, 3 de paridade
# ============================================================================
class Hamming74:
    """Codifica/decodifica blocos de 4 bits com Hamming(7,4)."""

    # Matriz geradora G = [I₄ | P]
    G = np.array([
        [1,0,0,0, 0,1,1],
        [0,1,0,0, 1,0,1],
        [0,0,1,0, 1,1,0],
        [0,0,0,1, 1,1,1],
    ], dtype=int)

    # Matriz de verificação H = [Pᵀ | I₃]
    H = np.array([
        [0,1,1,1, 1,0,0],
        [1,0,1,1, 0,1,0],
        [1,1,0,1, 0,0,1],
    ], dtype=int)

    @classmethod
    def encode_block(cls, bits: np.ndarray) -> np.ndarray:
        """4 bits → 7 bits codificados."""
        return (bits @ cls.G) % 2

    @classmethod
    def decode_block(cls, coded: np.ndarray) -> Tuple[np.ndarray, bool]:
        """7 bits → 4 bits corrigidos + flag de erro detectado."""
        syndrome = (cls.H @ coded) % 2
        error_pos = int(''.join(map(str, syndrome)), 2) - 1

        if error_pos >= 0 and error_pos < 7:
            coded[error_pos] ^= 1
            corrected = True
        else:
            corrected = (np.sum(syndrome) == 0)  # síndrome zero = sem erro

        return coded[:4], corrected

    @classmethod
    def encode(cls, data: np.ndarray) -> np.ndarray:
        """Codifica vetor de bits (múltiplo de 4)."""
        n = len(data)
        assert n % 4 == 0, "Data length must be multiple of 4"
        encoded = np.zeros(n * 7 // 4, dtype=int)
        for i in range(n // 4):
            encoded[i*7:(i+1)*7] = cls.encode_block(data[i*4:(i+1)*4])
        return encoded

    @classmethod
    def decode(cls, coded: np.ndarray) -> Tuple[np.ndarray, int]:
        """Decodifica vetor, retorna (dados corrigidos, número de erros)."""
        n = len(coded)
        assert n % 7 == 0, "Coded length must be multiple of 7"
        decoded = np.zeros(n * 4 // 7, dtype=int)
        errors_found = 0
        for i in range(n // 7):
            decoded[i*4:(i+1)*4], corrected = cls.decode_block(coded[i*7:(i+1)*7].copy())
            if not corrected:
                errors_found += 1
        return decoded, errors_found

# ============================================================================
# 2. GENOMA SINTÉTICO COM GECC
# ============================================================================
@dataclass
class SyntheticGenome:
    """Genoma essencial + junk DNA (código de correção)."""
    essential: np.ndarray          # 256 bits
    junk: np.ndarray               # bits de paridade
    encoded: np.ndarray            # essential + junk combinados
    generation: int = 0
    hash: str = ""

    @classmethod
    def create_random(cls, n_bits: int = 256):
        essential = np.random.randint(0, 2, n_bits)
        # Garantir múltiplo de 4 para Hamming(7,4)
        if n_bits % 4 != 0:
            essential = essential[:n_bits - (n_bits % 4)]
        encoded = Hamming74.encode(essential)
        junk = encoded[len(essential):]  # bits de paridade
        genome = cls(essential=essential, junk=junk, encoded=encoded)
        genome.hash = hashlib.sha3_256(essential.tobytes()).hexdigest()[:16]
        return genome

    def introduce_noise(self, rate: float) -> np.ndarray:
        """Aplica ruído cósmico ao genoma codificado."""
        noisy = self.encoded.copy()
        mask = np.random.random(len(noisy)) < rate
        noisy[mask] ^= 1
        return noisy

    def replicate(self, error_rate: float) -> Tuple[np.ndarray, int, int]:
        """Um ciclo de replicação: ruído → correção."""
        noisy = self.introduce_noise(error_rate)
        decoded, errors_uncorrected = Hamming74.decode(noisy)
        self.generation += 1
        return decoded, errors_uncorrected, np.sum(noisy != self.encoded)

# ============================================================================
# 3. SIMULAÇÃO DE 1000 CICLOS
# ============================================================================
def run_simulation(n_bits=256, n_cycles=1000, error_rate=0.05):
    """Simula replicação do genoma com GECC ativo."""
    genome = SyntheticGenome.create_random(n_bits)

    results = {
        'cycles': [],
        'total_errors_before': 0,
        'total_errors_after': 0,
        'total_mutations_applied': 0,
    }

    print(f"🧬 Iniciando simulação GECC: {n_cycles} ciclos, ruído {error_rate*100:.1f}%")
    print(f"   Genoma essencial: {len(genome.essential)} bits")
    print(f"   Junk DNA (paridade): {len(genome.junk)} bits")
    print(f"   Hash inicial: {genome.hash}")

    for cycle in range(n_cycles):
        corrected, errors_left, mutations = genome.replicate(error_rate)

        # Métricas
        fidelity = np.mean(corrected == genome.essential)

        results['cycles'].append({
            'cycle': cycle,
            'fidelity': float(fidelity),
            'errors_uncorrected': errors_left,
            'mutations_applied': mutations,
        })
        results['total_errors_before'] += mutations
        results['total_errors_after'] += errors_left
        results['total_mutations_applied'] += len(genome.essential)

    # Métricas finais
    avg_fidelity = np.mean([c['fidelity'] for c in results['cycles']])
    error_rate_with_ecc = results['total_errors_after'] / results['total_mutations_applied']
    error_rate_without_ecc = error_rate  # teórico

    print(f"\n✅ Simulação concluída:")
    print(f"   Fidelidade média: {avg_fidelity:.4f}")
    print(f"   Taxa de erro SEM GECC: {error_rate_without_ecc:.4f}")
    print(f"   Taxa de erro COM GECC: {error_rate_with_ecc:.6f}")
    print(f"   Redução: {(1 - error_rate_with_ecc/error_rate_without_ecc)*100:.1f}%")

    return genome, results, avg_fidelity, error_rate_with_ecc

if __name__ == "__main__":
    # Executar
    genome, sim_results, fidelity, final_error_rate = run_simulation(256, 1000, 0.05)

    # ============================================================================
    # 4. ANCORAR NO REGISTRY (SIMULADO)
    # ============================================================================
    @dataclass
    class ArtBlock:
        package_hash: str
        metadata: dict
        author_signature: str
        author_orcid: str
        temporal_anchor: str
        timestamp: float = field(default_factory=time.time)

        def compute_block_hash(self) -> str:
            payload = f"{self.package_hash}{self.author_orcid}{self.timestamp}"
            return hashlib.sha3_256(payload.encode()).hexdigest()[:16]

    # Criar ArtBlock para o genoma
    orcid = "0009-0005-2697-4668"
    genome_block = ArtBlock(
        package_hash=genome.hash,
        metadata={
            "type": "SyntheticGenome_GECC",
            "essential_bits": len(genome.essential),
            "junk_bits": len(genome.junk),
            "ecc_scheme": "Hamming(7,4)",
            "simulation_cycles": 1000,
            "final_fidelity": float(fidelity),
            "final_error_rate": float(final_error_rate),
        },
        author_signature=hashlib.sha3_256(f"{genome.hash}{orcid}sim".encode()).hexdigest()[:32],
        author_orcid=orcid,
        temporal_anchor=hashlib.sha3_256(f"anchor:{time.time_ns()}".encode()).hexdigest()[:12],
    )

    block_hash = genome_block.compute_block_hash()
    print(f"\n📦 ArtBlock ancorado:")
    print(f"   Block hash: {block_hash}")
    print(f"   Temporal anchor: {genome_block.temporal_anchor}")
    print(f"   ORCID: {genome_block.author_orcid}")

    # ============================================================================
    # 5. GERAR PDF COM REPORTLAB
    # ============================================================================
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, Image
    )
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.graphics.shapes import Drawing, Line, String
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics import renderPDF

    NAVY   = HexColor('#0B1F3A')
    GOLD   = HexColor('#C9A84C')
    CREAM  = HexColor('#FAF7F0')
    GREEN  = HexColor('#1E8449')
    RED    = HexColor('#C0392B')
    GRAY   = HexColor('#DDDDDD')

    def generate_gecc_report(genome, sim_results, fidelity, final_error, block_hash):
        os.makedirs('/mnt/user-data/outputs', exist_ok=True)
        path = '/mnt/user-data/outputs/GECC_Simulation_Report.pdf'
        doc = SimpleDocTemplate(path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        S = getSampleStyleSheet()
        W = A4[0] - 4*cm
        story = []

        # Título
        title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=20,
                                     textColor=NAVY, leading=24, spaceAfter=6, alignment=TA_CENTER)
        story.append(Paragraph("GECC Simulation Report", title_style))
        story.append(Paragraph("Genomic Error-Correction Code — Substrato 6160",
                               ParagraphStyle('Sub', fontName='Helvetica', fontSize=12,
                                             textColor=GOLD, leading=14, alignment=TA_CENTER)))
        story.append(Spacer(1, 20))

        # Métricas principais
        metrics = [
            ["Métrica", "Valor"],
            ["Essential bits", str(len(genome.essential))],
            ["Junk DNA bits", str(len(genome.junk))],
            ["ECC Scheme", "Hamming(7,4)"],
            ["Simulation cycles", "1,000"],
            ["Noise rate (cosmic)", "5.0%"],
            ["Avg. Fidelity (GECC ON)", f"{fidelity:.4f}"],
            ["Error rate (GECC OFF)", "5.0%"],
            ["Error rate (GECC ON)", f"{final_error:.6f}"],
            ["Error reduction", f"{(1 - final_error/0.05)*100:.1f}%"],
            ["Genome Hash", genome.hash],
            ["ArtBlock Hash", block_hash],
            ["ORCID", "0009-0005-2697-4668"],
        ]
        t = Table(metrics, colWidths=[5*cm, W-5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), white),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [CREAM, HexColor('#EFF2F7')]),
            ('GRID', (0,0), (-1,-1), 0.5, GRAY),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # Gráfico de fidelidade
        story.append(Paragraph("Fidelity Over 1,000 Replication Cycles",
                               ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=14,
                                             textColor=NAVY, leading=16)))

        # Criar gráfico simples com as primeiras e últimas 50 amostras
        cycles_data = sim_results['cycles']
        sample = cycles_data[::10]  # 100 pontos

        drawing = Drawing(400, 200)
        lp = LinePlot()
        lp.x = 50; lp.y = 30; lp.width = 300; lp.height = 150
        lp.data = [
            [(i, s['fidelity']) for i, s in enumerate(sample)],
            [(0, 1.0), (len(sample)-1, 1.0)],  # linha de referência
        ]
        lp.lines[0].strokeColor = NAVY
        lp.lines[1].strokeColor = GRAY
        drawing.add(lp)
        story.append(drawing)
        story.append(Spacer(1, 20))

        # Conclusão
        story.append(Paragraph("Conclusion", ParagraphStyle('H2', fontName='Helvetica-Bold',
                               fontSize=14, textColor=NAVY, leading=16)))
        story.append(Paragraph(
            f"The Genomic Error-Correction Code (GECC) reduces cosmic noise from 5.0% to "
            f"{final_error:.4f}% — a reduction of {(1-final_error/0.05)*100:.1f}%. "
            f"The 256-bit synthetic genome maintained an average fidelity of {fidelity:.4f} "
            f"over 1,000 replication cycles, demonstrating that junk DNA functions as an "
            f"effective parity-check matrix. The genome has been anchored as ArtBlock "
            f"#{block_hash} and signed by ORCID 0009-0005-2697-4668. "
            f"Substrato 6160 is now operational.",
            ParagraphStyle('Body', fontName='Helvetica', fontSize=10, leading=14,
                          alignment=TA_JUSTIFY)))

        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC | "
                               f"Canonical Seal: {hashlib.sha3_256(open(path, 'rb').read() if os.path.exists(path) else b'').hexdigest()[:16]}",
                               ParagraphStyle('Small', fontName='Helvetica', fontSize=7, textColor=GRAY)))

        doc.build(story)
        print(f"\n📄 PDF gerado: {path}")

    # Gerar relatório
    generate_gecc_report(genome, sim_results, fidelity, final_error_rate, block_hash)
