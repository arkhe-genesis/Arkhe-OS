package frontends

// Constantes biofísicas canônicas
const (
    R = 8.314462618    // J/(mol·K)
    T = 310.15         // K (37°C, temperatura fisiológica)
    F = 96485.33212    // C/mol
)

func nernstFactor(n int) float64 {
    return (R * T) / (float64(n) * F) * 1000 // mV
}
