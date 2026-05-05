import numpy as np
from scipy import stats

def dickey_fuller_test(series: np.ndarray, max_lag: int = None) -> dict:
    from statsmodels.tsa.stattools import adfuller
    result = adfuller(series, maxlag=max_lag, autolag='AIC')
    return {
        'adf_statistic': result[0],
        'p_value': result[1],
        'critical_values': result[4],
        'is_stationary': result[1] < 0.05
    }

def verify_convergence(
    step_gaps: np.ndarray,
    step_energies: np.ndarray,
    kolmogorov_limit: float,
    confidence: float = 0.95
) -> dict:
    results = {}
    df_result = dickey_fuller_test(step_gaps[-200:])
    results['gap_stationarity'] = df_result

    t = np.arange(len(step_gaps))
    slope, intercept, r_value, p_value, std_err = stats.linregress(t[-100:], step_gaps[-100:])
    results['gap_trend'] = {
        'slope': slope,
        'p_value': p_value,
        'decreasing': slope < 0 and p_value < 0.05
    }

    final_energy = step_energies[-1]
    energy_std = np.std(step_energies[-50:]) if len(step_energies) >= 50 else 0
    ci_lower = final_energy - stats.norm.ppf((1+confidence)/2) * energy_std / np.sqrt(50)
    results['kolmogorov_reached'] = ci_lower >= kolmogorov_limit
    results['final_energy_ci'] = (ci_lower, final_energy + stats.norm.ppf((1+confidence)/2) * energy_std / np.sqrt(50))

    return results
