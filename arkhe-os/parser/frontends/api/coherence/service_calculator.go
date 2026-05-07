package coherence

import (
	"arkhe/parser/frontends/api/models"
)

// CalculateServiceCoherence evaluates how "coherent" the API is
// Metrics: Consistency, Security Cover, Resource matching
func CalculateServiceCoherence(api *models.APIInfrastructure) float64 {
	if len(api.Endpoints) == 0 {
		return 0.0
	}

	secureEndpoints := 0
	for _, ep := range api.Endpoints {
		if ep.RequiresAuth {
			secureEndpoints++
		}
	}

	securityRatio := float64(secureEndpoints) / float64(len(api.Endpoints))

	// Simplified formula for demo
	coherence := (securityRatio * 0.5) + 0.5
	return coherence
}
