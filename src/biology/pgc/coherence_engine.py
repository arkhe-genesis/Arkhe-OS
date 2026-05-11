import numpy as np
import pandas as pd
from scipy import stats

class KuramotoCoherence:
    def global_coherence(self, phase_data: pd.DataFrame):
        """
        Computes weighted lambda_2 (Kuramoto order parameter).
        lambda_2 = |sum(w_j * e^(i*theta_j))| / sum(w_j)
        """
        phases = phase_data['theta'].values
        weights = phase_data['weight'].values

        complex_sum = np.sum(weights * np.exp(1j * phases))
        total_weight = np.sum(weights)

        z = complex_sum / total_weight if total_weight > 0 else 0
        lambda_2 = np.abs(z)

        return {
            'lambda_2': lambda_2,
            'mean_phase': np.angle(z) if lambda_2 > 0 else 0
        }

    def null_coherence_test(self, phase_data: pd.DataFrame, n_perms=500):
        """
        Robust Null Test: Permute BETA values between SNPs.
        This breaks both direction and magnitude correlations while keeping the SE structure.
        """
        real_lambda = self.global_coherence(phase_data)['lambda_2']
        null_lambdas = []

        betas = phase_data['BETA'].values
        weights = phase_data['weight'].values

        for _ in range(n_perms):
            shuffled_betas = np.random.permutation(betas)
            # Recompute phases with shuffled betas
            shuffled_phases = np.angle(shuffled_betas + 1j * weights)
            z_null = np.sum(weights * np.exp(1j * shuffled_phases)) / np.sum(weights)
            null_lambdas.append(np.abs(z_null))

        null_lambdas = np.array(null_lambdas)
        p_val = np.sum(null_lambdas >= real_lambda) / n_perms
        z_score = (real_lambda - np.mean(null_lambdas)) / np.std(null_lambdas)

        return {
            'real_lambda': real_lambda,
            'null_mean': np.mean(null_lambdas),
            'null_std': np.std(null_lambdas),
            'p_value': p_val,
            'z_score': z_score
        }

    def detect_phase_transitions_cusum(self, sliding_coherence: pd.DataFrame):
        """
        Change point detection using CUSUM to identify 'Zones of Genomic Instability'.
        """
        data = sliding_coherence['local_lambda'].values
        z = (data - np.mean(data)) / np.std(data)
        cusum = np.cumsum(z)

        # Detect significant deviations
        changes = []
        for i in range(1, len(cusum)):
            if abs(cusum[i] - cusum[i-1]) > 2.0:
                changes.append(i)
        return changes

    def cross_disorder_coherence(self, gwas_a: pd.DataFrame, gwas_b: pd.DataFrame):
        """
        Calculates the phase coherence between two disorders (e.g., SCZ and BIP).
        Measures if the effect of common SNPs is harmonic (same direction) or discordant.
        """
        # Inner join on common SNPs
        common = pd.merge(gwas_a, gwas_b, on='SNP', suffixes=('_A', '_B'))

        if common.empty:
            return {'lambda_ab': 0.0, 'n_common': 0, 'mean_phase_diff': 0.0}

        # Phase alignment (delta_theta = theta_A - theta_B)
        w_a = common['weight_A'].values
        w_b = common['weight_B'].values
        combined_weight = w_a * w_b

        complex_a = np.exp(1j * common['theta_A'].values)
        complex_b = np.exp(1j * common['theta_B'].values)

        # Complex phase differential: e^{j(theta_A - theta_B)}
        phase_diff = complex_a * np.conj(complex_b)

        # Global Cross Coherence (λ_AB)
        lambda_ab = np.abs(np.sum(combined_weight * phase_diff)) / np.sum(combined_weight)

        return {
            'lambda_ab': lambda_ab,
            'n_common': len(common),
            'mean_phase_diff': np.angle(np.sum(combined_weight * phase_diff))
        }

class CrossDisorderAnalyzer:
    """
    Analyzes gene overlap and phase consistency between multiple disorders.
    """
    def __init__(self):
        self.disorder_genes = {} # {name: set(genes)}
        self.disorder_data = {}

    def add_disorder(self, name, df_gwas, snp_to_gene):
        genes = set(snp_to_gene.values())
        self.disorder_genes[name] = genes
        self.disorder_data[name] = df_gwas

    def get_overlap(self, name_a, name_b):
        if name_a in self.disorder_genes and name_b in self.disorder_genes:
            return self.disorder_genes[name_a].intersection(self.disorder_genes[name_b])
        return set()
