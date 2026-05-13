import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from Bio import Entrez
import random

from .extremophile_genome import ExtremophileGenome

# Always set email for Entrez
Entrez.email = "arkhe.os.biological@arkhe.com"

class JSONCache:
    def __init__(self, cache_file: str = "ncbi_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any):
        self.cache[key] = value
        self._save_cache()

class NCBIJGIClient:
    def __init__(self, cache_file: str = "ncbi_cache.json"):
        self.cache = JSONCache(cache_file)

    def fetch_extremophile_ids(self, term: str = "extremophile[All Fields] AND genome[All Fields]", max_results: int = 50) -> List[str]:
        cache_key = f"search_{term}_{max_results}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        print(f"Fetching IDs from NCBI for term: '{term}'...")
        try:
            handle = Entrez.esearch(db="nucleotide", term=term, retmax=max_results)
            record = Entrez.read(handle)
            id_list = record.get("IdList", [])
            self.cache.set(cache_key, id_list)
            return id_list
        except Exception as e:
            print(f"Error fetching from NCBI: {e}")
            return []

    def fetch_genome_summary(self, genome_id: str) -> Dict[str, Any]:
        cache_key = f"summary_{genome_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            handle = Entrez.esummary(db="nucleotide", id=genome_id)
            records = Entrez.read(handle)
            if records:
                record = records[0]
                # Convert DictElement to standard dict for caching
                summary = {k: str(v) for k, v in record.items()}
                self.cache.set(cache_key, summary)
                return summary
            return {}
        except Exception as e:
            print(f"Error fetching summary for {genome_id}: {e}")
            return {}

    def fetch_genome_fasta(self, genome_id: str) -> str:
        cache_key = f"fasta_{genome_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            handle = Entrez.efetch(db="nucleotide", id=genome_id, rettype="fasta", retmode="text")
            fasta_data = handle.read()
            self.cache.set(cache_key, fasta_data)
            return fasta_data
        except Exception as e:
            print(f"Error fetching FASTA for {genome_id}: {e}")
            return ""

    def extract_features(self, summary: Dict[str, Any]) -> Tuple[float, List[str], float]:
        """
        Automated feature extraction (heuristics/dummy logic for simulation).
        """
        title = summary.get("Title", "").lower()

        # Determine type heuristics
        junk_pct = random.uniform(10.0, 40.0)
        ecc_mechs = ["Hamming(7,4)"]
        rad_res = random.uniform(0.1, 0.5)

        if "radiodurans" in title or "radio" in title:
            rad_res = random.uniform(0.8, 1.0)
            junk_pct = random.uniform(30.0, 60.0)
            ecc_mechs.append("Berlekamp-Massey")
            ecc_mechs.append("RecA-mediated")

        if "thermus" in title or "thermo" in title:
            rad_res = random.uniform(0.5, 0.7)
            junk_pct = random.uniform(20.0, 45.0)
            ecc_mechs.append("Hsp70 Chaperone")

        if "halo" in title:
            junk_pct = random.uniform(15.0, 35.0)
            ecc_mechs.append("Osmotic-ECC")

        return junk_pct, ecc_mechs, rad_res

    def fetch_jgi_genome(self, genus: str) -> Dict[str, Any]:
        """
        Stub for JGI Genome Portal API.
        Real JGI requires XML login and cookie passing to fetch from standard portal.
        """
        print(f"Querying JGI Genome Portal for {genus}...")
        return {
            "source": "JGI",
            "genus": genus,
            "simulated_features": {
                "junk_percentage": random.uniform(20.0, 50.0),
                "ecc_mechanisms": ["RecA", "Rad51"],
                "rad_resistance": random.uniform(0.3, 0.9)
            }
        }

    def build_dataset(self, target_size: int = 50) -> List[ExtremophileGenome]:
        ids = self.fetch_extremophile_ids(max_results=target_size)
        dataset = []

        print(f"Building dataset for {len(ids)} extremophile genomes...")
        for i, gid in enumerate(ids):
            summary = self.fetch_genome_summary(gid)
            title = summary.get("Title", f"Unknown Genome {gid}")

            # Extract features
            junk_pct, ecc_mechs, rad_res = self.extract_features(summary)

            # Determine type
            gtype = "extremophile"
            if "radio" in title.lower(): gtype = "radiophile"
            elif "thermo" in title.lower(): gtype = "thermophile"
            elif "halo" in title.lower(): gtype = "halophile"

            # Fetch a snippet of the sequence (or full if small)
            fasta = self.fetch_genome_fasta(gid)
            seq_snippet = "".join(fasta.split("\n")[1:])[:100] if fasta else ""

            genome = ExtremophileGenome(
                id=gid,
                name=title[:50] + "..." if len(title) > 50 else title,
                type=gtype,
                sequence=seq_snippet,
                junk_percentage=round(junk_pct, 2),
                ecc_mechanisms=ecc_mechs,
                rad_resistance=round(rad_res, 2),
                go_annotations=["GO:0006974", "GO:0006281"]  # DNA repair, response to DNA damage
            )
            dataset.append(genome)

            if (i+1) % 10 == 0:
                print(f"  Processed {i+1}/{len(ids)}")

            time.sleep(0.34) # NCBI rate limit: 3 requests per second

        return dataset
