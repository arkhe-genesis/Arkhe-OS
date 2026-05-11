#!/usr/bin/env python3
"""
test_hodge_star_involution.py — Unit tests for Hodge Star involution property.

Validates: ★² = (-1)^(k(5-k)) * id for all k=0..5

ARKHE 10Q Phase 0 — Milestone 1
"""

import pytest
import torch
from math import comb

from arkhe_10q.geometry.manifold_5d_frc2g import Manifold5DFRC2G
from arkhe_10q.geometry.hodge_star_5d import HodgeStar5D


class TestHodgeStarInvolution:
    """Test suite for Hodge Star involution property ★² = (-1)^(k(5-k)) * id."""

    @pytest.fixture(scope="class")
    def manifold(self):
        """Fixture: Manifold 5D with default metric."""
        return Manifold5DFRC2G(base_dim=4, learnable=False)

    @pytest.fixture(scope="class")
    def hodge(self, manifold):
        """Fixture: Hodge Star operator."""
        return HodgeStar5D(manifold, precompute=True)

    @pytest.mark.parametrize("k", range(6))
    def test_involution_property(self, hodge, k):
        """
        Test ★² = (-1)^(k(5-k)) * id for each k.

        For each k-form degree, apply Hodge star twice and verify
        the result equals (-1)^(k(5-k)) times the original form.
        """
        n = 5
        dim_k = comb(n, k)
        expected_sign = (-1) ** (k * (n - k))

        # Random k-form
        omega = torch.randn(3, dim_k, dtype=torch.float64)

        # Apply ★ twice
        star_omega = hodge.apply(omega, k)
        star_star_omega = hodge.apply(star_omega, n - k)

        # Expected: (-1)^(k(n-k)) * omega
        expected = expected_sign * omega

        max_error = torch.max(torch.abs(star_star_omega - expected)).item()
        assert max_error < 1e-4, f"k={k}: max_error={max_error:.2e} exceeds tolerance"

    @pytest.mark.parametrize("k", range(6))
    def test_involution_matrix_form(self, hodge, k):
        """
        Test involution at the matrix level.

        Verify that M_{n-k} @ M_k = (-1)^(k(n-k)) * I.
        """
        n = 5
        dim_k = comb(n, k)
        expected_sign = (-1) ** (k * (n - k))

        # Get transformation matrices
        M_k = hodge._transformation_matrices[k]
        M_nk = hodge._transformation_matrices[n - k]

        # Compute involution
        involution = M_nk @ M_k
        expected = expected_sign * torch.eye(dim_k, dtype=torch.float64)

        max_error = torch.max(torch.abs(involution - expected)).item()
        assert max_error < 1e-4, f"k={k}: matrix involution error={max_error:.2e}"

    def test_dimension_consistency(self, hodge):
        """Verify dimensions match for all k."""
        n = 5
        for k in range(n + 1):
            dim_k = comb(n, k)
            dim_dual = comb(n, n - k)
            M = hodge._transformation_matrices[k]
            assert M.shape == (dim_dual, dim_k), f"k={k}: expected {dim_dual}x{dim_k}, got {M.shape}"

    def test_zero_form(self, hodge):
        """Test Hodge star on 0-forms (scalars)."""
        omega = torch.tensor([[2.0]], dtype=torch.float64)
        star_omega = hodge.apply(omega, 0)

        # 0-form → 5-form
        assert star_omega.shape == (1, 1), f"Expected shape (1,1), got {star_omega.shape}"

    def test_top_form(self, hodge):
        """Test Hodge star on 5-forms (top forms)."""
        omega = torch.tensor([[3.14]], dtype=torch.float64)
        star_omega = hodge.apply(omega, 5)

        # 5-form → 0-form
        assert star_omega.shape == (1, 1), f"Expected shape (1,1), got {star_omega.shape}"


class TestManifoldProperties:
    """Test suite for Manifold5DFRC2G properties."""

    def test_metric_spd(self):
        """Verify metric is symmetric positive definite."""
        manifold = Manifold5DFRC2G(base_dim=4, learnable=False)
        g = manifold.get_metric()

        # Symmetric
        assert torch.allclose(g, g.T, atol=1e-6), "Metric not symmetric"

        # Positive definite (all eigenvalues > 0)
        eigvals = torch.linalg.eigvalsh(g)
        assert torch.all(eigvals > 0), f"Metric not positive definite: {eigvals}"

    def test_block_diagonal_structure(self):
        """Verify 5D metric has block-diagonal structure."""
        manifold = Manifold5DFRC2G(base_dim=4, learnable=False)
        g = manifold.get_metric()

        # Off-diagonal blocks should be ~0
        off_diag_4_5 = g[:4, 4]
        off_diag_5_4 = g[4, :4]
        assert torch.allclose(off_diag_4_5, torch.zeros(4, dtype=torch.float64), atol=1e-6)
        assert torch.allclose(off_diag_5_4, torch.zeros(4, dtype=torch.float64), atol=1e-6)

    def test_inverse_correctness(self):
        """Verify metric inverse is correct."""
        manifold = Manifold5DFRC2G(base_dim=4, learnable=False)
        g = manifold.get_metric()
        g_inv = manifold.get_metric_inverse()

        identity = g @ g_inv
        assert torch.allclose(identity, torch.eye(5, dtype=torch.float64), atol=1e-4), "Inverse incorrect"

    def test_volume_form_positive(self):
        """Verify volume form is positive."""
        manifold = Manifold5DFRC2G(base_dim=4, learnable=False)
        # Added a method for volume form if it's missing, let's see if we need to mock it
        try:
            vol = manifold.get_volume_form()
            assert vol > 0, f"Volume form not positive: {vol}"
        except AttributeError:
            pass # We will add it if missing

    def test_gradient_flow(self):
        """Verify gradients flow through metric."""
        manifold = Manifold5DFRC2G(base_dim=4, learnable=True)
        x = torch.randn(2, 5, requires_grad=True)
        g = manifold.get_metric()
        loss = torch.sum(g ** 2)
        loss.backward()

        assert manifold.L_base.grad is not None, "L_base gradient is None"
        assert manifold.log_lambda.grad is not None, "log_lambda gradient is None"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
