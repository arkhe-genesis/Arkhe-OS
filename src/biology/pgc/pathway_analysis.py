import numpy as np
import pandas as pd
from scipy import stats
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class PathwayEnrichmentAnalyzer:
    """
    Pathway Enrichment for Arkhe-PGC v3.0.
    Supports GMT files and hypergeometric testing with FDR (Benjamini-Hochberg).
    """
    def __init__(self):
        self.pathways = {}

    def load_gmt(self, path):
        """Loads Gene Matrix Transposed (.gmt) file."""
        with open(path, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) > 2:
                    name = parts[0]
                    genes = set(parts[2:])
                    self.pathways[name] = genes
        logger.info(f"Loaded {len(self.pathways)} pathways.")

    def run_enrichment(self, query_genes, background_genes, p_cutoff=0.05):
        query_set = set(query_genes)
        bg_set = set(background_genes)

        M = len(bg_set)
        n = len(query_set)

        results = []
        for name, genes in self.pathways.items():
            pathway_in_bg = genes.intersection(bg_set)
            N = len(pathway_in_bg)
            k = len(genes.intersection(query_set))

            if k > 0:
                p_val = stats.hypergeom.sf(k - 1, M, N, n)
                results.append({
                    "Pathway": name,
                    "Hits": k,
                    "Size": N,
                    "P-value": p_val,
                    "Enrichment": (k/n) / (N/M) if N > 0 else 0
                })

        df = pd.DataFrame(results)
        if not df.empty:
            df['FDR_adj_P'] = stats.false_discovery_control(df['P-value'].values, method='bh')
            return df[df['FDR_adj_P'] < p_cutoff].sort_values("FDR_adj_P")
        return df

    def calculate_pathway_coherence(self, pathway_genes, phase_df, snp_to_gene):
        """
        Evaluates if the SNPs regulating the genes of a pathway are in harmony.
        """
        relevant_snps = [snp for snp, gene in snp_to_gene.items() if gene in pathway_genes]
        df_path = phase_df[phase_df['SNP'].isin(relevant_snps)]

        if len(df_path) < 3:
            return np.nan

        weights = df_path['weight'].values
        # Use theta angle directly
        phases = df_path['theta'].values
        complex_vecs = np.exp(1j * phases)

        lambda_path = np.abs(np.sum(weights * complex_vecs)) / np.sum(weights)
        return lambda_path

class SingleCellEqtlMapper:
    """
    Maps SNPs to genes using single-cell eQTL data.
    """
    def __init__(self, sc_eqtl_file=None):
        self.sc_eqtl = {} # {snp: {cell_type: gene}}
        self.cell_type_genes = defaultdict(set)
        if sc_eqtl_file:
            self.load_sc_eqtl(sc_eqtl_file)

    def load_sc_eqtl(self, filepath):
        df = pd.read_csv(filepath, sep='\t')
        for _, row in df.iterrows():
            snp = row['SNP']
            gene = row['GENE']
            ct = row['CELL_TYPE']
            if snp not in self.sc_eqtl:
                self.sc_eqtl[snp] = {}
            self.sc_eqtl[snp][ct] = gene
            self.cell_type_genes[ct].add(gene)

    def get_mapping(self, cell_type):
        mapping = {}
        for snp, ct_data in self.sc_eqtl.items():
            if cell_type in ct_data:
                mapping[snp] = ct_data[cell_type]
        return mapping

class GTExMapper:
    """
    Maps SNPs to regulated genes using GTEx eQTL data.
    """
    def __init__(self):
        self.eqtl_map = {}

    def load_eqtl_data(self, path):
        df = pd.read_csv(path, sep='\t')
        self.eqtl_map = df.sort_values('PVALUE').drop_duplicates('SNP').set_index('SNP')['GENE'].to_dict()

    def map_snps(self, snps):
        return {snp: self.eqtl_map.get(snp) for snp in snps if snp in self.eqtl_map}
