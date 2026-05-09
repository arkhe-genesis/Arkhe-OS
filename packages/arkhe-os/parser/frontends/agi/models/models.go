package models

type Value struct {
	ID                  string   `json:"id"`
	Name                string   `json:"name"`
	Category            string   `json:"category"`
	Priority            string   `json:"priority"`
	Weight              float64  `json:"weight"`
	FormalExpression    string   `json:"formal_expression,omitempty"`
	PotentialConflicts  []string `json:"potential_conflicts,omitempty"`
	ConflictResolution  string   `json:"conflict_resolution,omitempty"`
	Description         string   `json:"description,omitempty"`
}

type SuccessCriterion struct {
	Description string  `json:"description"`
	MetricName  string  `json:"metric_name"`
	Threshold   float64 `json:"threshold"`
	Operator    string  `json:"operator"`
}

type Goal struct {
	ID                 string                   `json:"id"`
	Name               string                   `json:"name"`
	Priority           string                   `json:"priority"`
	SuccessCriteria    []SuccessCriterion       `json:"success_criteria"`
	ResponsibleModules []string                 `json:"responsible_modules"`
	Description        string                   `json:"description,omitempty"`
	Metrics            []map[string]interface{} `json:"metrics,omitempty"`
	Constraints        []string                 `json:"constraints,omitempty"`
}

type VerifiableProperty struct {
	Name                string `json:"name"`
	FormalSpecification string `json:"formal_specification"`
	VerificationMethod  string `json:"verification_method"`
}

type Implementation struct {
	Type             string                 `json:"type"`
	Configuration    map[string]interface{} `json:"configuration"`
	FallbackBehavior string                 `json:"fallback_behavior,omitempty"`
	Framework        string                 `json:"framework,omitempty"`
	ModelPath        string                 `json:"model_path,omitempty"`
}

type SafetyMechanism struct {
	ID                   string               `json:"id"`
	Name                 string               `json:"name"`
	MechanismType        string               `json:"type"`
	Implementation       Implementation       `json:"implementation"`
	VerifiableProperties []VerifiableProperty `json:"verifiable_properties"`
	Description          string               `json:"description,omitempty"`
}

type Module struct {
	ID             string                   `json:"id"`
	Name           string                   `json:"name"`
	Type           string                   `json:"type"`
	Inputs         []map[string]interface{} `json:"inputs,omitempty"`
	Outputs        []map[string]interface{} `json:"outputs,omitempty"`
	Implementation *Implementation          `json:"implementation,omitempty"`
	Dependencies   []string                 `json:"dependencies,omitempty"`
	ProvidesTo     []string                 `json:"provides_to,omitempty"`
	Configuration  map[string]interface{}   `json:"configuration,omitempty"`
	Description    string                   `json:"description,omitempty"`
}

type Spec struct {
	Name             string                 `json:"name"`
	ArchitectureType string                 `json:"architecture_type"`
	Values           []Value                `json:"values"`
	Goals            []Goal                 `json:"goals"`
	Modules          []Module               `json:"modules"`
	SafetyMechanisms []SafetyMechanism      `json:"safety_mechanisms"`
	MetaCognition    map[string]interface{} `json:"meta_cognition"`
	Environment      interface{}            `json:"environment"`
}
