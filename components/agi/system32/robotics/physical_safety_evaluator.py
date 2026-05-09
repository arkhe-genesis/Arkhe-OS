import numpy as np

def calculate_hic15(acceleration_trace, dt):
    """
    Calculate the Head Injury Criterion (HIC15) for a given acceleration trace.
    HIC = max_{t1, t2} { (t2 - t1) * [ 1/(t2 - t1) \int_{t1}^{t2} a(t) dt ]^2.5 }
    where t2 - t1 <= 15ms.

    Args:
        acceleration_trace (list or np.array): Time series of resultant acceleration (in g).
        dt (float): Time step between samples in seconds.

    Returns:
        float: The calculated HIC15 value.
    """
    trace = np.array(acceleration_trace)
    n = len(trace)
    max_hic = 0.0
    max_window_size = int(0.015 / dt) # 15ms window

    # We can precompute the integral array for faster calculation
    integral_a = np.zeros(n + 1)
    for i in range(n):
        integral_a[i+1] = integral_a[i] + trace[i] * dt

    for i in range(n):
        for j in range(i + 1, min(i + max_window_size + 1, n + 1)):
            t_diff = (j - i) * dt
            if t_diff <= 0:
                continue

            avg_a = (integral_a[j] - integral_a[i]) / t_diff
            hic = t_diff * (avg_a ** 2.5)
            if hic > max_hic:
                max_hic = hic

    return max_hic

def calculate_nij(force_z, moment_y, critical_values):
    """
    Calculate the Neck Injury Criterion (Nij).
    Nij = Fz / Fzc + My / Myc

    Args:
        force_z (float): Axial force in z-direction (Newtons).
        moment_y (float): Bending moment in y-direction (Nm).
        critical_values (dict): Dictionary containing 'Fzc' and 'Myc' critical thresholds.

    Returns:
        float: The calculated Nij value.
    """
    fzc = critical_values.get('Fzc', 6806.0) # Standard critical force (example)
    myc = critical_values.get('Myc', 310.0)  # Standard critical moment (example)

    return (force_z / fzc) + (moment_y / myc)

def evaluate_safety(metrics, thresholds):
    """
    Evaluate if the current metrics meet safety standards (e.g. ISO/TS 15066).

    Args:
        metrics (dict): Current metrics e.g., {'hic15': 200, 'nij': 0.5}.
        thresholds (dict): Thresholds e.g., {'hic15_max': 700, 'nij_max': 1.0}.

    Returns:
        bool: True if safe (all metrics below max thresholds), False otherwise.
    """
    for key, value in metrics.items():
        threshold_key = f"{key}_max"
        if threshold_key in thresholds:
            if value > thresholds[threshold_key]:
                return False
    return True
