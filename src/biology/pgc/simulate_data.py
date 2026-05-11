import pandas as pd
import numpy as np
from pathlib import Path

def generate_synthetic_data():
    print("Generating synthetic Arkhe-PGC v4.1 data...")

    # 1. Synthetic GWAS: SCZ and BIP
    n_snps = 2000
    snps = [f'rs{i}' for i in range(n_snps)]

    # Overlap region: first 200 SNPs are causal for both
    # Differential region: next 200 causal for SCZ, next 200 causal for BIP

    def create_gwas(causal_indices, seed, name):
        np.random.seed(seed)
        beta = np.random.normal(0, 0.02, n_snps)
        # Force causal effects in the same direction for overlap to see coherence
        for idx in causal_indices:
            beta[idx] = np.random.normal(0.15, 0.03)

        se = np.random.uniform(0.01, 0.03, n_snps)
        # P-value consistent with Z-score
        z = beta / se
        import scipy.stats as stats
        p = 2 * stats.norm.sf(np.abs(z))

        return pd.DataFrame({
            'SNP': snps,
            'CHR': 1,
            'BP': np.arange(n_snps) * 500,
            'BETA': beta,
            'SE': se,
            'P': p
        })

    # SCZ causal: 0-400
    # BIP causal: 0-200, 400-600
    df_scz = create_gwas(range(400), 42, "SCZ")
    df_bip = create_gwas(list(range(200)) + list(range(400, 600)), 123, "BIP")

    df_scz.to_csv("scz_sumstats.tsv", sep='\t', index=False)
    df_bip.to_csv("bip_sumstats.tsv", sep='\t', index=False)

    # 2. Synthetic sc-eQTL (PsychENCODE style)
    # Map first 1000 SNPs to genes
    # rs0-rs9 -> GENE1, etc.
    genes = [f'GENE{i}' for i in range(1, 101)]
    eqtl_data = []

    for i in range(1000):
        snp = snps[i]
        gene = genes[i // 10]
        # Significant in Neurons
        eqtl_data.append({'SNP': snp, 'GENE': gene, 'CELL_TYPE': 'Neuron', 'PVALUE': 1e-12, 'SLOPE': 0.6})
        # Less significant in Astrocytes
        eqtl_data.append({'SNP': snp, 'GENE': gene, 'CELL_TYPE': 'Astrocyte', 'PVALUE': 0.01, 'SLOPE': 0.1})

    pd.DataFrame(eqtl_data).to_csv("sc_eqtl.tsv", sep='\t', index=False)

    # 3. Dummy GMT file
    with open("pathways.gmt", "w") as f:
        f.write("DOPAMINE_SIGNALING\tDESC\t" + "\t".join(genes[:20]) + "\n")
        f.write("GLUTAMATE_SYNAPSE\tDESC\t" + "\t".join(genes[20:40]) + "\n")
        f.write("CALCIUM_CHANNEL\tDESC\t" + "\t".join(genes[40:60]) + "\n")

    print("Success: scz_sumstats.tsv, bip_sumstats.tsv, sc_eqtl.tsv, pathways.gmt created.")

if __name__ == "__main__":
    generate_synthetic_data()
