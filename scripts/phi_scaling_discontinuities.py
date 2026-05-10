#!/usr/bin/env python3
"""
phi_scaling_discontinuities.py — Test Prediction C: P(s) kinks at s_k = 200·φ^k bp
"""
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import chi2
import cooler
import logging

PHI = (1 + np.sqrt(5)) / 2
NUCLEOSOME_REPEAT = 200  # bp
PHI_LAYERS = [NUCLEOSOME_REPEAT * (PHI**k) for k in range(0, 8)]  # 200 bp to ~5 Mb

def compute_contact_probability(cool_path, chrom, start, end, max_s=1_000_000):
    """Compute P(s) from balanced Hi‑C/Micro‑C data."""
    c = cooler.Cooler(cool_path)
    mat = c.matrix(balance=True).fetch(f'{chrom}:{start}-{end}')

    # Compute contact probability as function of genomic distance
    distances = []
    contacts = []
    n = mat.shape[0]

    for i in range(n):
        for j in range(i+1, min(i+max_s//c.binsize, n)):
            s = (j - i) * c.binsize  # genomic distance in bp
            if s > max_s:
                break
            distances.append(s)
            contacts.append(mat[i,j])

    # Bin by log‑distance
    log_s = np.log10(distances)
    log_bins = np.linspace(log_s.min(), log_s.max(), 100)
    bin_centers = 10**((log_bins[:-1] + log_bins[1:]) / 2)

    P_s = []
    for i in range(len(log_bins)-1):
        mask = (log_s >= log_bins[i]) & (log_s < log_bins[i+1])
        if mask.sum() > 10:
            P_s.append(np.mean(np.array(contacts)[mask]))
        else:
            P_s.append(np.nan)

    return bin_centers[:-1], np.array(P_s)

def fit_piecewise_powerlaw_with_phi_breaks(s, P_s, phi_breaks=None):
    """
    Fit P(s) with breakpoints fixed at φ‑based lengths.
    Model: log P = -α_k · log s + C_k for s in [break_k, break_{k+1}]
    """
    if phi_breaks is None:
        phi_breaks = PHI_LAYERS

    # Filter to observed range
    valid_breaks = [b for b in phi_breaks if s.min() < b < s.max()]
    if len(valid_breaks) < 2:
        return None

    # Piecewise linear fit in log‑log space
    log_s = np.log10(s)
    log_P = np.log10(P_s)
    mask = ~np.isnan(log_P)
    log_s, log_P = log_s[mask], log_P[mask]

    # Fit each segment
    alphas = []
    for k in range(len(valid_breaks)-1):
        seg_mask = (s >= valid_breaks[k]) & (s < valid_breaks[k+1])
        if seg_mask.sum() < 20:
            continue
        # Linear regression: log P = -α · log s + C
        coeffs = np.polyfit(log_s[seg_mask], log_P[seg_mask], 1)
        alphas.append(-coeffs[0])  # α = -slope

    if len(alphas) < 2:
        return None

    return {
        'breakpoints': valid_breaks,
        'alphas': alphas,
        'n_segments': len(alphas)
    }

def test_phi_breaks_vs_null(cool_path, chrom, start, end, n_null=1000):
    """Test whether φ‑based breakpoints fit better than random breakpoints."""
    s, P_s = compute_contact_probability(cool_path, chrom, start, end)

    # Fit with φ‑based breakpoints
    phi_fit = fit_piecewise_powerlaw_with_phi_breaks(s, P_s)
    if not phi_fit:
        return None

    # Compute residual sum of squares for φ model
    def piecewise_model(log_s, *params):
        # params: [C_0, α_0, C_1, α_1, ...] for each segment
        result = np.zeros_like(log_s)
        valid_breaks = phi_fit['breakpoints']
        for k, (b_start, b_end) in enumerate(zip(valid_breaks[:-1], valid_breaks[1:])):
            mask = (s >= b_start) & (s < b_end)
            if mask.sum() == 0:
                continue
            C_k = params[2*k]
            alpha_k = params[2*k + 1]
            result[mask] = C_k - alpha_k * log_s[mask]
        return result

    # Fit φ model to get RSS
    log_s = np.log10(s)
    log_P = np.log10(P_s)
    mask = ~np.isnan(log_P)

    # Initial params from segment fits
    init_params = []
    for k, (b_start, b_end) in enumerate(zip(phi_fit['breakpoints'][:-1], phi_fit['breakpoints'][1:])):
        seg_mask = (s >= b_start) & (s < b_end) & mask
        if seg_mask.sum() > 10:
            coeffs = np.polyfit(log_s[seg_mask], log_P[seg_mask], 1)
            init_params.extend([coeffs[1], -coeffs[0]])  # C, α
        else:
            init_params.extend([0, 1])  # fallback

    try:
        popt, _ = curve_fit(piecewise_model, log_s[mask], log_P[mask], p0=init_params)
        rss_phi = np.sum((log_P[mask] - piecewise_model(log_s[mask], *popt))**2)
    except:
        return None

    # Null model: random breakpoints (same number, log‑uniform distribution)
    rss_null = []
    n_segments = len(phi_fit['alphas'])
    for _ in range(n_null):
        # Generate random breakpoints in log‑space
        log_min, log_max = np.log10(s.min()), np.log10(s.max())
        rand_breaks = 10**np.sort(np.random.uniform(log_min, log_max, n_segments-1))
        rand_breaks = [s.min()] + list(rand_breaks) + [s.max()]

        # Fit piecewise model with random breaks
        init_params_null = []
        for k in range(len(rand_breaks)-1):
            seg_mask = (s >= rand_breaks[k]) & (s < rand_breaks[k+1]) & mask
            if seg_mask.sum() > 10:
                coeffs = np.polyfit(log_s[seg_mask], log_P[seg_mask], 1)
                init_params_null.extend([coeffs[1], -coeffs[0]])
            else:
                init_params_null.extend([0, 1])

        try:
            popt_null, _ = curve_fit(piecewise_model, log_s[mask], log_P[mask], p0=init_params_null)
            rss = np.sum((log_P[mask] - piecewise_model(log_s[mask], *popt_null))**2)
            rss_null.append(rss)
        except:
            continue

    if len(rss_null) < 100:
        return None

    # Likelihood ratio test: φ model should have significantly lower RSS
    rss_null = np.array(rss_null)
    p_value = np.mean(rss_null <= rss_phi)  # One‑tailed: φ should be better

    return {
        'rss_phi': rss_phi,
        'rss_null_mean': rss_null.mean(),
        'rss_null_std': rss_null.std(),
        'p_value': p_value,
        'phi_breakpoints': phi_fit['breakpoints'],
        'phi_alphas': phi_fit['alphas'],
        'n_segments': n_segments
    }

if __name__ == '__main__':
    import sys
    cool_path = sys.argv[1]  # Micro‑C .cool file
    chrom = sys.argv[2]      # e.g., 'chr1'
    start, end = int(sys.argv[3]), int(sys.argv[4])

    result = test_phi_breaks_vs_null(cool_path, chrom, start, end)

    if result:
        print(f"✅ Scaling Exponent Test:")
        print(f"   φ‑based breakpoints: {[f'{b/1000:.1f}kb' for b in result['phi_breakpoints']]}")
        print(f"   Exponents α_k: {result['phi_alphas']}")
        print(f"   RSS (φ model): {result['rss_phi']:.2f}")
        print(f"   RSS (null mean ± std): {result['rss_null_mean']:.2f} ± {result['rss_null_std']:.2f}")
        print(f"   p‑value (φ better than random): {result['p_value']:.4f}")

        if result['p_value'] < 0.05:
            print(f"   🎯 SIGNIFICANT: φ‑based breakpoints preferred (p < 0.05)")
        else:
            print(f"   ⚠️  Not significant: φ‑model not preferred over random")
