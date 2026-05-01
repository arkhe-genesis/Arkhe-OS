import re

with open("arkhe_adaptive_pointing_controller.py", "r") as f:
    content = f.read()

# Fix the minor logical slip where we pass `self.mekf.b_est` instead of `omega_meas - self.mekf.b_est` for error_omega
content = content.replace("tau_wheels, tau_cmd = self.lqr.compute_torque(theta_err, self.mekf.b_est, alpha_true)", "tau_wheels, tau_cmd = self.lqr.compute_torque(theta_err, omega_meas - self.mekf.b_est, alpha_true)")

with open("arkhe_adaptive_pointing_controller.py", "w") as f:
    f.write(content)
