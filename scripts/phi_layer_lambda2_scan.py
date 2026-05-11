#!/usr/bin/env python3
"""
phi_layer_lambda2_scan.py — Test Prediction A: φ‑based connectivity maxima in TADs
"""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import eigsh
from scipy.stats import ks_2samp, norm
import cooler
import logging

PHI = (1 + np.sqrt(5)) / 2
MIN_TAD_LENGTH = 500_000  # 500 kb
MAX_TAD_LENGTH = 2_000_000  # 2 Mb
BIN_SIZE_RANGE = np.logspace(3, 5.3, 150)  # 1 kb to 200 kb

def compute_normalized_laplacian_lambda2(contact_matrix):
    """Compute λ₂ of symmetric normalized Laplacian."""
    # Avoid division by zero
    degrees = np.array(contact_matrix.sum(axis=1)).flatten()
    degrees = np.maximum(degrees, 1e-10)

    # D^{-1/2} C D^{-1/2}
    D_inv_sqrt = diags(1.0 / np.sqrt(degrees))
    L_sym = csr_matrix(np.eye(contact_matrix.shape[0])) - D_inv_sqrt @ contact_matrix @ D_inv_sqrt

    # Compute second smallest eigenvalue (λ₁ = 0 by construction)
    # Use shift-invert for better convergence on smallest eigenvalues
    try:
        eigvals = eigsh(L_sym, k=3, which='SM', tol=1e-6, return_eigenvectors=False)
        return eigvals[1]  # λ₂
    except:
        # Fallback: dense eigendecomposition for small matrices
        if contact_matrix.shape[0] < 500:
            L_dense = L_sym.toarray()
            eigvals = np.linalg.eigvalsh(L_dense)
            return eigvals[1]
        return None

def scan_tad_for_phi_signal(cool_path, chrom, start, end, tad_id):
    """Scan a single TAD for φ‑based λ₂ maxima."""
    c = cooler.Cooler(cool_path)
    try:
        mat = c.matrix(balance=True).fetch(f'{chrom}:{start}-{end}')
    except:
        return None

    L = end - start
    results = []

    for b in BIN_SIZE_RANGE:
        n_bins = int(L / b)
        if n_bins < 5 or n_bins > 200:  # Avoid too coarse or too fine
            continue

        # Bin the contact matrix
        binned = np.zeros((n_bins, n_bins))
        for i in range(n_bins):
            for j in range(n_bins):
                i0, i1 = int(i*b), int((i+1)*b)
                j0, j1 = int(j*b), int((j+1)*b)
                if i0 < mat.shape[0] and j0 < mat.shape[1]:
                    binned[i,j] = mat[i0:i1, j0:j1].mean()

        # Ensure symmetry
        binned = (binned + binned.T) / 2

        # Compute λ₂
        lambda2 = compute_normalized_laplacian_lambda2(binned)
        if lambda2 is not None:
            results.append({'bin_size': b, 'lambda2': lambda2, 'n_bins': n_bins})

    if not results:
        return None

    df = pd.DataFrame(results)

    # Find local maxima of λ₂
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(df['lambda2'].values, distance=5, prominence=0.01)

    # Check if any peak aligns with φ‑based binning
    phi_ratios = [L / (PHI**k) for k in range(1, 12)]
    best_match = None
    best_deviation = float('inf')

    for peak_idx in peaks:
        b_peak = df.iloc[peak_idx]['bin_size']
        for phi_b in phi_ratios:
            deviation = abs(np.log(b_peak / phi_b))
            if deviation < best_deviation:
                best_deviation = deviation
                best_match = {'bin_size': b_peak, 'phi_ratio': phi_b, 'deviation': deviation}

    return {
        'tad_id': tad_id,
        'length': L,
        'lambda2_max': df['lambda2'].max(),
        'best_phi_match': best_match,
        'deviation_from_phi': best_deviation if best_match else None,
        'n_peaks': len(peaks)
    }

def aggregate_phi_signal_across_tads(cool_path, tad_bed, output_csv):
    """Aggregate φ‑signal test across many TADs."""
    results = []
    tads = pd.read_csv(tad_bed, sep='\t', header=None,
                      names=['chrom', 'start', 'end', 'tad_id'])

    for _, row in tads.iterrows():
        if row['end'] - row['start'] < MIN_TAD_LENGTH:
            continue
        result = scan_tad_for_phi_signal(cool_path, row['chrom'], row['start'], row['end'], row['tad_id'])
        if result and result['best_phi_match']:
            results.append(result)

    # Statistical test: are deviations from φ smaller than expected by chance?
    deviations = [r['deviation_from_phi'] for r in results if r['deviation_from_phi'] is not None]

    # Generate null: random bin sizes with same distribution
    null_deviations = []
    for _ in range(1000):
        null_devs = []
        for r in results:
            L = r['length']
            # Random bin size from same log‑uniform distribution
            b_rand = 10**np.random.uniform(np.log10(1000), np.log10(200000))
            # Find closest power of integer
            best_null_dev = float('inf')
            for k in range(1, 12):
                int_ratio = k
                deviation = abs(np.log(b_rand / (L / int_ratio)))
                best_null_dev = min(best_null_dev, deviation)
            null_devs.append(best_null_dev)
        null_deviations.append(np.mean(null_devs))

    observed_mean = np.mean(deviations)
    p_value = np.mean([nd >= observed_mean for nd in null_deviations])

    # Save results
    pd.DataFrame(results).to_csv(output_csv, index=False)

    return {
        'n_tads_tested': len(results),
        'mean_deviation_from_phi': observed_mean,
        'p_value_ks': p_value,
        'phi_aligned_tads': sum(1 for d in deviations if d < np.log(PHI)/2)
    }

if __name__ == '__main__':
    import sys
    cool_path = sys.argv[1]  # e.g., 'GM12878_30kb.cool'
    tad_bed = sys.argv[2]    # e.g., 'tads_GM12878.bed'
    output = sys.argv[3]     # e.g., 'phi_scan_results.csv'

    stats = aggregate_phi_signal_across_tads(cool_path, tad_bed, output)
    print(f"✅ φ‑Layer Scan Complete:")
    print(f"   TADs tested: {stats['n_tads_tested']}")
    print(f"   Mean log‑deviation from φ: {stats['mean_deviation_from_phi']:.3f}")
    print(f"   p‑value (KS test vs null): {stats['p_value_ks']:.4f}")
    print(f"   TADs aligned with φ (dev < log(φ)/2): {stats['phi_aligned_tads']}")
