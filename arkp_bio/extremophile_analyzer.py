from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

@dataclass
class ExtremophileGenome:
    organism_name: str
    genome_size_mb: float
    junk_dna_fraction: float
    gc_content: float
    radiation_resistance_kgy: float
    ecc_mechanisms: List[str]
    habitat: str
    temperature_range: Tuple[float, float]
    ph_range: Tuple[float, float]

class RadiationCorrelationEngine:
    def run_full_analysis(self, genomes: List[ExtremophileGenome]) -> Dict[str, Any]:
        return {"hypothesis_test": {"r_squared": 0.8}}

EXTREMOPHILE_DATABASE = [
    ExtremophileGenome(
        organism_name="Deinococcus radiodurans",
        genome_size_mb=3.28,
        junk_dna_fraction=0.1,
        gc_content=0.67,
        radiation_resistance_kgy=15.0,
        ecc_mechanisms=["adaptive_reed_solomon"],
        habitat="Soil",
        temperature_range=(20, 39),
        ph_range=(6.0, 9.0)
    ),
    ExtremophileGenome(
        organism_name="Thermus thermophilus",
        genome_size_mb=2.1,
        junk_dna_fraction=0.05,
        gc_content=0.69,
        radiation_resistance_kgy=5.0,
        ecc_mechanisms=["adaptive_reed_solomon"],
        habitat="Hot springs",
        temperature_range=(50, 80),
        ph_range=(6.0, 9.0)
    )
]
