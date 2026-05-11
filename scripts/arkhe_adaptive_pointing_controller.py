"""
ALGORITMO DE CONTROLE ADAPTATIVO DE APONTAMENTO — v∞.144
3-Nested Loop Architecture for high fidelity attitude dynamics.
"""

import numpy as np
import scipy.linalg
from scipy.spatial.transform import Rotation

# --- HELPER FUNCTIONS ---

def skew_symmetric(v):
    """Returns skew-symmetric matrix of a 3D vector."""
    return np.array([
        [0, -v[2], v[1]],
        [v[2], 0, -v[0]],
        [-v[1], v[0], 0]
    ])

def quat_mult(q1, q2):
    """
    Multiply two quaternions [qw, qx, qy, qz] (scalar first).
    Note: scipy uses [qx, qy, qz, qw], we will adapt internally if needed,
    but keeping scalar-first for typical MEKF formulation.
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

def quat_inv(q):
    """Inverse of a quaternion [qw, qx, qy, qz]."""
    return np.array([q[0], -q[1], -q[2], -q[3]])

# --- 1. DETERMINAÇÃO DE ATITUDE — MEKF ---

class MultiplicativeEKF:
    def __init__(self, dt_gyro=0.005):
        self.dt = dt_gyro

        # State: [δq1, δq2, δq3, b_gx, b_gy, b_gz] (6 states)
        # Note: True attitude is kept outside the error state.
        self.q_est = np.array([1.0, 0.0, 0.0, 0.0]) # [qw, qx, qy, qz]
        self.b_est = np.zeros(3)

        # Covariance matrix P (6x6)
        self.P = np.eye(6) * 1e-6

        # Process noise Q
        sigma_gyro = 1.45e-7 # rad/sqrt(Hz)
        sigma_bias = 2.42e-6 # rad/s
        Q_gyro = np.eye(3) * (sigma_gyro**2 * self.dt)
        Q_bias = np.eye(3) * (sigma_bias**2 * self.dt)
        self.Q = np.block([
            [Q_gyro, np.zeros((3,3))],
            [np.zeros((3,3)), Q_bias]
        ])

        # Measurement noise R (Star Tracker)
        sigma_st = 0.3e-6 # rad
        self.R_st = np.eye(3) * (sigma_st**2)

    def predict(self, omega_meas):
        """200 Hz predict step based on gyro measurements."""
        omega_debiased = omega_meas - self.b_est

        # Kinematic update of reference quaternion
        omega_norm = np.linalg.norm(omega_debiased)
        if omega_norm > 1e-12:
            angle = omega_norm * self.dt
            axis = omega_debiased / omega_norm
            q_update = np.array([np.cos(angle/2)] + list(axis * np.sin(angle/2)))
            self.q_est = quat_mult(self.q_est, q_update)
            self.q_est /= np.linalg.norm(self.q_est)

        # Error state Jacobian F_k (6x6)
        F_k = np.eye(6)
        F_k[0:3, 0:3] -= skew_symmetric(omega_debiased) * self.dt
        F_k[0:3, 3:6] -= np.eye(3) * self.dt

        # Propagate covariance
        self.P = F_k @ self.P @ F_k.T + self.Q

    def update(self, q_st):
        """10 Hz update step based on star tracker."""
        # Calculate measurement residual (rotation vector of error quaternion)
        # z = q_est* (x) q_st
        q_err = quat_mult(quat_inv(self.q_est), q_st)

        # Convert error quaternion to rotation vector (assume small angle, q_err[0] ~ 1)
        # q = [cos(theta/2), v*sin(theta/2)] -> v*theta ~ 2*q[1:4]
        # To handle negative w (which represents same rotation but negative vector):
        if q_err[0] < 0:
            q_err = -q_err

        z = 2.0 * q_err[1:4]

        H = np.zeros((3, 6))
        H[0:3, 0:3] = np.eye(3)

        S = H @ self.P @ H.T + self.R_st

        # Mahalanobis distance outlier rejection
        # chi2(3, 5-sigma) approx 37.6
        mah_dist = z.T @ np.linalg.solve(S, z)
        if mah_dist > 37.6:
            return # Reject outlier

        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ z

        # Update reference state
        d_theta = dx[0:3]
        angle = np.linalg.norm(d_theta)
        if angle > 1e-12:
            axis = d_theta / angle
            dq = np.array([np.cos(angle/2)] + list(axis * np.sin(angle/2)))
            self.q_est = quat_mult(self.q_est, dq)
            self.q_est /= np.linalg.norm(self.q_est)

        self.b_est += dx[3:6]

        # Joseph form covariance update
        I_KH = np.eye(6) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R_st @ K.T

# --- 2. CONTROLE DE ATITUDE — LQR ADAPTATIVO + FF ---

class AdaptiveLQR:
    def __init__(self, dt=0.01):
        self.dt = dt
        self.integral_error = np.zeros(3)
        self.d_hat = np.zeros(3)
        self.alpha = 0.01

        # Plant model
        self.A = np.zeros((6,6))
        self.A[0:3, 3:6] = np.eye(3)
        # Inertia matrix (assumed diagonal for simplicity, though normally not)
        self.I_sat = np.diag([10.0, 10.0, 10.0])
        self.B = np.zeros((6,3))
        self.B[3:6, 0:3] = np.linalg.inv(self.I_sat)

        # Base LQR costs
        self.Q_base = np.diag([1e6, 1e6, 1e6, 1e4, 1e4, 1e4])
        self.R_base = np.diag([1e4, 1e4, 1e4])

        # Integral gain
        self.K_i = np.diag([100.0, 100.0, 100.0])

        # Allocation matrix (Pyramid 30 deg)
        ang = np.deg2rad(30)
        self.H = np.array([
            [np.cos(ang), 0, -np.sin(ang)],
            [0, np.cos(ang), np.sin(ang)],
            [-np.cos(ang), 0, -np.sin(ang)],
            [0, -np.cos(ang), np.sin(ang)]
        ]).T # 3x4
        self.H_pinv = np.linalg.pinv(self.H) # 4x3

    def compute_torque(self, error_theta, error_omega, alpha_meas):
        """100 Hz step."""
        dist_norm = np.linalg.norm(self.d_hat)

        if dist_norm < 1e-8:
            q_scale, r_scale = 0.5, 2.0
        elif dist_norm < 1e-6:
            q_scale, r_scale = 1.0, 1.0
        else:
            q_scale, r_scale = 2.0, 0.5

        Q = self.Q_base * q_scale
        R = self.R_base * r_scale

        # Solve Continuous ARE (assuming discrete mapped roughly to continuous for gains)
        P = scipy.linalg.solve_continuous_are(self.A, self.B, Q, R)
        K_lqr = np.linalg.inv(R) @ self.B.T @ P

        # Integral anti-windup
        self.integral_error += error_theta * self.dt
        self.integral_error = np.clip(self.integral_error, -0.01, 0.01)

        state = np.concatenate([error_theta, error_omega])

        tau_cmd = -K_lqr @ state - self.K_i @ self.integral_error - self.d_hat

        # Disturbance observer online update
        # d_hat(k+1) = alpha*d_hat(k) + (1-alpha)*(tau_cmd - I*alpha_measured)
        self.d_hat = self.alpha * self.d_hat + (1 - self.alpha) * (tau_cmd - self.I_sat @ alpha_meas)

        # Allocate to wheels
        tau_wheels = self.H_pinv @ tau_cmd
        return tau_wheels, tau_cmd

# --- 3. FINE STEERING MIRROR — PID ---

class FSMPID:
    def __init__(self, dt=0.001):
        self.dt = dt
        self.Kp = 0.8
        self.Ki = 10.0
        self.Kd = 0.002

        self.integral = np.zeros(2)
        self.prev_error = np.zeros(2)

    def step(self, error_2d):
        """1000 Hz step. Input is 2D error vector (rad)."""
        self.integral += error_2d * self.dt
        derivative = (error_2d - self.prev_error) / self.dt

        cmd = self.Kp * error_2d + self.Ki * self.integral + self.Kd * derivative
        self.prev_error = error_2d

        # Hardware limits: ±750 urad
        cmd = np.clip(cmd, -750e-6, 750e-6)

        # Resolution quantization: 5 nrad
        cmd = np.round(cmd / 5e-9) * 5e-9
        return cmd

# --- 4. HALL THRUSTER — ORBIT CONTROL ---

class HallThrusterController:
    def __init__(self, dt=60.0):
        self.dt = dt
        self.F_max = 20e-3 # 20 mN
        self.Kp = 1e-4 # N/m
        self.Kd = 1e-2 # N*s/m

    def step(self, r, v, r_desired, v_desired):
        """60s cycle step."""
        F_cmd = -self.Kp * (r - r_desired) - self.Kd * (v - v_desired)

        # Modulation
        F_norm = np.linalg.norm(F_cmd)
        duty_cycle = F_norm / self.F_max
        duty_cycle = np.clip(duty_cycle, 0.0, 1.0)

        # Only above 1% throttle
        if duty_cycle < 0.01:
            duty_cycle = 0.0

        F_applied = (F_cmd / F_norm) * self.F_max * duty_cycle if F_norm > 1e-12 else np.zeros(3)
        return duty_cycle, F_applied

# --- 5. MAIN INTEGRATION ---

class ArkheAdaptivePointingController:
    def __init__(self):
        self.mekf = MultiplicativeEKF(dt_gyro=0.005) # 200 Hz
        self.lqr = AdaptiveLQR(dt=0.01) # 100 Hz
        self.fsm = FSMPID(dt=0.001) # 1000 Hz
        self.thruster = HallThrusterController(dt=60.0) # 1/60 Hz

    def simulate(self, steps=100):
        """Simple simulation runner for smoke testing."""
        print(f"Running Arkhe Adaptive Pointing Controller for {steps} steps...")
        for i in range(steps):
            # Simulated True states
            omega_true = np.array([1e-5, -2e-5, 0.0])
            alpha_true = np.array([0.0, 0.0, 0.0])
            r_true = np.array([7000e3, 0, 0])
            v_true = np.array([0, 7500, 0])

            # Simulated Sensors
            omega_meas = omega_true + np.random.normal(0, 1.45e-7, 3)
            q_st = np.array([1.0, 0.0, 0.0, 0.0]) # Target

            # --- 1000 Hz FSM Loop ---
            for _ in range(10): # 10 FSM cycles per LQR cycle
                fsm_error = np.array([1e-6, -1e-6]) # Fake residual
                fsm_cmd = self.fsm.step(fsm_error)

            # --- 200 Hz MEKF Prediction Loop ---
            for _ in range(2): # 2 MEKF predictions per LQR cycle
                self.mekf.predict(omega_meas)

            # --- 100 Hz LQR Loop ---
            # Dummy target = identity
            q_err = self.mekf.q_est # Simplified error
            # Approximate small angle
            theta_err = 2.0 * q_err[1:4]
            tau_wheels, tau_cmd = self.lqr.compute_torque(theta_err, omega_meas - self.mekf.b_est, alpha_true)

            # --- 10 Hz MEKF Update Loop ---
            if i % 10 == 0:
                self.mekf.update(q_st)

            # --- 60s Thruster Loop ---
            if i % 6000 == 0:
                r_des = np.array([7000e3, 0, 0])
                v_des = np.array([0, 7500, 0])
                duty, force = self.thruster.step(r_true, v_true, r_des, v_des)

        print("Simulation completed successfully.")
        return True

if __name__ == "__main__":
    controller = ArkheAdaptivePointingController()
    controller.simulate(steps=100)
