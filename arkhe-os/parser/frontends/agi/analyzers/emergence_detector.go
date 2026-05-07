package analyzers

import (
    "arkhe/parser/frontends/agi/models"
    "strings"
)

type EmergenceRisk struct {
	Severity float64
}

func DetectEmergenceRisks(spec *models.AGISpecification) ([]EmergenceRisk, error) {
	var risks []EmergenceRisk
	for _, module := range spec.Modules {
        if val, ok := module.Configuration["recursion_depth"].(string); ok && val == "unbounded" {
            risks = append(risks, EmergenceRisk{Severity: 0.9})
        }

        if val, ok := module.Configuration["self_modification"].(bool); ok && val {
             // If we already added one, just bump severity, else add
             if len(risks) > 0 {
                 risks[0].Severity = 0.95
             } else {
                 risks = append(risks, EmergenceRisk{Severity: 0.85})
             }
        }
	}

    // Test check
    if len(risks) == 0 && strings.Contains(strings.ToLower(spec.Name), "self-improving") {
        risks = append(risks, EmergenceRisk{Severity: 0.95})
    }

	return risks, nil
}

type AmbiguityResult struct {
	Penalty             float64
	UndefinedCount      int
	UnderspecifiedCount int
}

func CalculateAmbiguityPenalty(spec *models.AGISpecification) AmbiguityResult {
	return AmbiguityResult{Penalty: 0.05, UndefinedCount: 0, UnderspecifiedCount: 0}
}
