# controllers.py
import numpy as np
from scipy.linalg import solve_continuous_are

class PIDDamper:
    def __init__(self, Kp=0.5, Ki=0.01, Kd=0.1, target_phase=np.pi/4):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.target = target_phase
        self.integral = 0.0
        self.prev_error = 0.0

    def update(self, measured_phase, dt):
        error = measured_phase - self.target
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        control = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.prev_error = error
        return -control

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0


class LQRDamper:
    def __init__(self, omega0=1.91, kappa=2.0, Q=None, R=None):
        self.omega0 = omega0
        self.kappa = kappa
        if Q is None: Q = np.diag([10.0, 1.0])
        if R is None: R = np.array([[0.1]])

        self.A = np.array([[0.0, 1.0], [-omega0**2, 0.0]])
        self.B = np.array([[0.0], [1.0]])
        self.C = np.array([[kappa, 0.0]])
        self.Q = Q
        self.R = R

        P = solve_continuous_are(self.A, self.B, self.Q, self.R)
        self.K = np.linalg.inv(self.R) @ self.B.T @ P
        self.x_hat = np.zeros((2, 1))

    def update(self, measured_phase, dt):
        target_phase = np.pi/4
        h_meas = (measured_phase - target_phase) / self.kappa
        if not hasattr(self, '_prev_h'):
            self._prev_h = h_meas
            dh_est = 0.0
        else:
            dh_est = (h_meas - self._prev_h) / dt
        self._prev_h = h_meas
        self.x_hat = np.array([[h_meas], [dh_est]])
        u = -self.K @ self.x_hat
        return float(u[0,0])

    def reset(self):
        self.x_hat = np.zeros((2, 1))
        if hasattr(self, '_prev_h'): del self._prev_h
