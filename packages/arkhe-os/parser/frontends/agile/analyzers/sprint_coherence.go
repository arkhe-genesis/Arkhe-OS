package analyzers

import (
	"math"

	"arkhe/parser/frontends/agile/models"
)

func ExtractVelocities(sprints []models.Sprint) []float64 {
	var velocities []float64
	for _, s := range sprints {
		if s.Velocity > 0 {
			velocities = append(velocities, s.Velocity)
		}
	}
	return velocities
}

func CalculateVelocityStability(velocities []float64) float64 {
	if len(velocities) < 2 {
		return 1.0
	}

	mean := 0.0
	for _, v := range velocities {
		mean += v
	}
	mean /= float64(len(velocities))

	if mean == 0 {
		return 0.0
	}

	variance := 0.0
	for _, v := range velocities {
		diff := v - mean
		variance += diff * diff
	}
	variance /= float64(len(velocities))

	stdDev := math.Sqrt(variance)
	cv := stdDev / mean

	// Stability is 1 - CV (capped between 0 and 1)
	stability := 1.0 - cv
	if stability < 0 {
		stability = 0
	}
	return stability
}
