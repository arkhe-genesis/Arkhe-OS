package chrono

type TemporalFlexEngine struct {
	coherence float64
}

func NewTemporalFlexEngine() *TemporalFlexEngine {
	return &TemporalFlexEngine{}
}

func (e *TemporalFlexEngine) SetCoherence(c float64) {
	e.coherence = c
}

func (e *TemporalFlexEngine) CompressTime(t1, t2, factor float64) map[string]float64 {
	latency := (t2 - t1) / factor
	causal_consistency := e.coherence * 1.2
	if causal_consistency > 1.0 {
		causal_consistency = 1.0
	}
	return map[string]float64{
		"effective_latency":  latency,
		"causal_consistency": causal_consistency,
	}
}
