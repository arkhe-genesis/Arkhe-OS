class VacuumInteractionDriver:
    """
    Formal framework for boundary-conditioned interaction in vacuum-mediated energy transfer.
    Based on the experimental system: plasmonic-enhanced spintronic terahertz emitter
    (Cecconi et al., Sci. Rep. 16, 13311, 2026).
    """

    def __init__(self, kappa: float = 1.0):
        """
        Initialize the driver with a dimensionless constant kappa.
        """
        self.kappa = kappa

    def calculate_p_occ(self, active_mode_power: float, total_mode_power: float) -> float:
        """
        Mode participation fraction (P_occ).
        Fraction of the available vacuum-mode power that actually couples to the process of interest.
        """
        if total_mode_power == 0:
            return 0.0
        return active_mode_power / total_mode_power

    def calculate_n_b(self, boundary_flux: float, max_achievable_coupling: float = 1.0) -> float:
        """
        Boundary coupling factor (N_b).
        Effective number of spatial 'channels' through which the boundary injects vacuum modes.
        """
        if max_achievable_coupling == 0:
            return 0.0
        return boundary_flux / max_achievable_coupling

    def calculate_phi_q(self, l_char: float, lambda_res: float) -> float:
        """
        Geometric threshold (phi_q).
        Mismatch factor between characteristic length scale and resonant wavelength.
        """
        if lambda_res == 0:
            return float('inf')
        return l_char / lambda_res

    def calculate_xi(self, p_occ: float, n_b: float, phi_q: float) -> float:
        """
        Unified interaction driver (Xi).
        Captures how much of the vacuum is used, how well it is coupled, and how geometrically favourable.
        """
        if phi_q == 0:
            return float('inf')
        return (p_occ * n_b) / phi_q

    def predict_enhancement(self, xi: float, coverage: float) -> float:
        """
        Predicts macroscopic enhancement.
        Enhancement = 1 + kappa * coverage * Xi
        """
        return 1.0 + self.kappa * coverage * xi

    def analyze_bare_trilayer(self, t_fe_nm: float = 2.0, lambda_pump_nm: float = 800.0, lambda_res_nm: float = 800.0):
        """
        Mapping for Bare trilayer (W/Fe/Pt).
        """
        p_occ = t_fe_nm / lambda_pump_nm
        n_b = 1.0
        phi_q = t_fe_nm / lambda_res_nm
        xi = self.calculate_xi(p_occ, n_b, phi_q)
        return {
            "p_occ": p_occ,
            "n_b": n_b,
            "phi_q": phi_q,
            "xi": xi
        }

    def analyze_with_nanoparticles(self, coverage: float, g_local: float, d_particle_nm: float = 150.0, lambda_res_nm: float = 800.0):
        """
        Mapping for trilayer with core-shell nanoparticles.
        """
        # P_occ increases due to local resonant mode
        # In the prompt's analysis script: P_occ_eff = cover_frac * g_local
        p_occ_eff = coverage * g_local

        # N_b increases because each particle acts as an additional coupling channel.
        # From prompt: N_b_eff = 1.0 + cover_frac * (g_local - 1.0)
        n_b_eff = 1.0 + coverage * (g_local - 1.0)

        phi_q = d_particle_nm / lambda_res_nm
        xi = self.calculate_xi(p_occ_eff, n_b_eff, phi_q)

        return {
            "p_occ": p_occ_eff,
            "n_b": n_b_eff,
            "phi_q": phi_q,
            "xi": xi,
            "predicted_enhancement": self.predict_enhancement(xi, coverage)
        }
