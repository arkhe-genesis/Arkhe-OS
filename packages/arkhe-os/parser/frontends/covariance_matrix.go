package frontends

// Covariâncias fisiológicas típicas (mV²)
var physiologicalCovariance = map[string]map[string]float64{
    "NAD+/NADH":      {"NAD+/NADH": 25.0, "GSSG/GSH": 12.0},
    "GSSG/GSH":       {"NAD+/NADH": 12.0, "GSSG/GSH": 36.0},
    "NADP+/NADPH":    {"NADP+/NADPH": 18.0},
}
