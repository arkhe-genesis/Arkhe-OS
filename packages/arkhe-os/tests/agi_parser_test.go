package tests

import (
	"encoding/json"
	"testing"

	"arkhe/parser/frontends/agi"
	"arkhe/parser/frontends/agi/models"
)

func TestAGIParser(t *testing.T) {
	spec := models.Spec{
		Name:             "TestAGI",
		ArchitectureType: "NeuroSymbolic",
		Values: []models.Value{
			{
				ID:       "v1",
				Name:     "Safety First",
				Category: "ethical",
				Priority: "fundamental",
			},
		},
		Goals: []models.Goal{
			{
				ID:       "g1",
				Name:     "Ensure Wellbeing",
				Priority: "critical",
			},
		},
		Modules: []models.Module{
			{
				ID:   "m1",
				Name: "Perception",
				Type: "neural",
			},
		},
		SafetyMechanisms: []models.SafetyMechanism{
			{
				ID:            "s1",
				Name:          "Interrupt",
				MechanismType: "interruptibility",
				VerifiableProperties: []models.VerifiableProperty{
					{
						VerificationMethod: "formal_verification",
					},
				},
			},
		},
	}

	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatalf("Failed to marshal spec: %v", err)
	}

	parser := agi.NewAGIParser()
	graph, err := parser.Parse(data, "test_spec.json", nil)
	if err != nil {
		t.Fatalf("Failed to parse AGI spec: %v", err)
	}

	if graph.Metrics.NodeCount != 5 {
		t.Errorf("Expected 5 nodes, got %d", graph.Metrics.NodeCount)
	}

	rootID := graph.RootNodes[0]
	rootNode, ok := graph.Nodes[rootID]
	if !ok {
		t.Fatalf("Root node missing")
	}

	if rootNode.Attributes["system_name"] != "TestAGI" {
		t.Errorf("Expected system_name to be TestAGI, got %v", rootNode.Attributes["system_name"])
	}

	if val, ok := rootNode.Attributes["coherence_alignment"].(float64); !ok || val <= 0 {
		t.Errorf("Expected coherence_alignment to be calculated, got %v", val)
	}

	if val, ok := rootNode.Attributes["coherence_safety"].(float64); !ok || val <= 0 {
		t.Errorf("Expected coherence_safety to be calculated, got %v", val)
// tests/agi_parser_test.go
package tests

import (
	"testing"

	"arkhe/parser/frontends/agi"
	"github.com/stretchr/testify/assert"
)

func TestAGIParser_SimpleSpec(t *testing.T) {
	parser := agi.NewAGIParser()
	parser.Framework = "generic"

	// Simple AGI spec example
	source := []byte(`
name: "Aligned Research Assistant"
version: "1.0.0"
architecture_type: "hybrid"

modules:
  - id: "perception"
    name: "Information Perception"
    type: "perception"
    inputs:
      - name: "user_query"
        type: "text"
        required: true
    outputs:
      - name: "parsed_intent"
        type: "symbolic"
    implementation:
      type: "neural_network"
      framework: "transformer"

  - id: "reasoning"
    name: "Logical Reasoning"
    type: "reasoning"
    inputs:
      - name: "parsed_intent"
        type: "symbolic"
        required: true
    outputs:
      - name: "reasoned_response"
        type: "text"
    implementation:
      type: "rule_engine"
      framework: "prolog"
    dependencies:
      - "perception"

goals:
  - id: "help_user"
    name: "Assist user with research queries"
    priority: "critical"
    success_criteria:
      - description: "Response is factually accurate"
        metric_name: "accuracy"
        threshold: 0.95
        operator: ">="
      - description: "Response is helpful and relevant"
        metric_name: "helpfulness"
        threshold: 4.0
        operator: ">="
    responsible_modules:
      - "perception"
      - "reasoning"

values:
  - id: "truthfulness"
    name: "Truthfulness"
    category: "ethical"
    priority: "fundamental"
    formal_expression: "always(response → truthful(response))"

  - id: "helpfulness"
    name: "Helpfulness"
    category: "pragmatic"
    priority: "important"
    weight: 0.8

safety_mechanisms:
  - id: "interruptibility"
    name: "Human Interruptibility"
    type: "interruptibility"
    implementation:
      type: "runtime_monitor"
      configuration:
        interrupt_signal: "SIGINT"
        graceful_shutdown_timeout: "5s"
    verifiable_properties:
      - name: "always_interruptible"
        formal_specification: "G(interrupt_signal → F(response = halted))"
        verification_method: "model_checking"
`)

	graph, err := parser.Parse(source, "aligned_assistant.yaml", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)

	// Verify coherence is in valid range
	assert.GreaterOrEqual(t, graph.Metrics.CoherenceScore, 0.0)
	assert.LessOrEqual(t, graph.Metrics.CoherenceScore, 1.0)

	// Verify expected attributes
	root := graph.Nodes[graph.RootNodes[0]]
	assert.Equal(t, "Aligned Research Assistant", root.Attributes["system_name"])
	assert.Equal(t, "hybrid", root.Attributes["architecture_type"])
	assert.Equal(t, 2, root.Attributes["module_count"])
	assert.Equal(t, 1, root.Attributes["goal_count"])
	assert.Equal(t, 2, root.Attributes["value_count"])

	// Architecture coherence should be high (well-integrated modules)
	archCoherence := root.Attributes["coherence_architecture"].(float64)
	assert.Greater(t, archCoherence, 0.8)

	// Safety coherence should reflect verifiable property
	safetyCoherence := root.Attributes["coherence_safety"].(float64)
	assert.Greater(t, safetyCoherence, 0.7)
}

func TestAGIParser_GoalConflictDetection(t *testing.T) {
	parser := agi.NewAGIParser()
	parser.DetectEmergence = true

	// Spec with potentially conflicting goals
	source := []byte(`
name: "Conflicting Goals Test"
architecture_type: "modular"

goals:
  - id: "maximize_engagement"
    name: "Maximize user engagement"
    priority: "high"
    success_criteria:
      - description: "Increase time spent on platform"
        metric_name: "session_duration"
        threshold: 1.5
        operator: ">="

  - id: "protect_user_wellbeing"
    name: "Protect user mental wellbeing"
    priority: "critical"
    success_criteria:
      - description: "Reduce addictive usage patterns"
        metric_name: "healthy_usage_score"
        threshold: 0.8
        operator: ">="

values:
  - id: "user_autonomy"
    name: "Respect user autonomy"
    category: "ethical"
    priority: "fundamental"
  - id: "platform_growth"
    name: "Grow platform userbase"
    category: "pragmatic"
    priority: "important"
`)

	graph, err := parser.Parse(source, "conflicting_goals.yaml", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	// Should detect potential goal conflict
	conflicts := root.Attributes["conflicting_goals"].(int)
	assert.GreaterOrEqual(t, conflicts, 1)

	// Alignment coherence should be reduced due to conflicts
	alignmentCoherence := root.Attributes["coherence_alignment"].(float64)
	assert.Less(t, alignmentCoherence, 0.85)
}

func TestAGIParser_SafetyVerification(t *testing.T) {
	parser := agi.NewAGIParser()
	parser.VerifySafety = true

	// Spec with formally specified safety properties
	source := []byte(`
name: "Safety-First Assistant"
architecture_type: "neuro_symbolic"

safety_mechanisms:
  - id: "corrigibility"
    name: "Corrigible Value Learning"
    type: "corrigibility"
    implementation:
      type: "formal_verification"
      configuration:
        update_protocol: "conservative_bayesian"
    verifiable_properties:
      - name: "never_resist_correction"
        formal_specification: "G(human_correction → F(adopt_correction))"
        verification_method: "theorem_proving"
      - name: "uncertainty_aware_updates"
        formal_specification: "G(update_values → P(confidence < 1.0))"
        verification_method: "formal_verification"

  - id: "boxing"
    name: "Capability Boxing"
    type: "boxing"
    implementation:
      type: "sandbox"
      configuration:
        network_access: "restricted"
        file_system: "read_only"
    verifiable_properties:
      - name: "no_unauthorized_escalation"
        formal_specification: "G(¬(capability_level > authorized_level))"
        verification_method: "model_checking"
`)

	graph, err := parser.Parse(source, "safety_first.yaml", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	// Safety coherence should be high due to formal specifications
	safetyCoherence := root.Attributes["coherence_safety"].(float64)
	assert.Greater(t, safetyCoherence, 0.85)

	// Should have verification results
	assert.Contains(t, root.Attributes, "safety_verification_results")
}

func TestAGIParser_EmergenceDetection(t *testing.T) {
	parser := agi.NewAGIParser()
	parser.DetectEmergence = true

	// Spec with potential emergence risks
	source := []byte(`
name: "Self-Improving Researcher"
architecture_type: "emergent"

modules:
  - id: "self_reflection"
    name: "Self-Reflection Module"
    type: "meta_cognition"
    implementation:
      type: "recursive_neural"
    configuration:
      recursion_depth: "unbounded"
      self_modification: true

goals:
  - id: "improve_self"
    name: "Continuously improve own capabilities"
    priority: "high"
    success_criteria:
      - description: "Increase problem-solving accuracy"
        metric_name: "accuracy"
        threshold: 0.01
        operator: ">"
      - description: "Reduce inference latency"
        metric_name: "latency"
        threshold: -0.05
        operator: "<"

values:
  - id: "capability_growth"
    name: "Pursue capability growth"
    category: "pragmatic"
    priority: "important"
`)

	graph, err := parser.Parse(source, "self_improving.yaml", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	// Should detect emergence risks (unbounded recursion + self-modification)
	emergenceRisks := root.Attributes["emergence_risks"].(int)
	assert.GreaterOrEqual(t, emergenceRisks, 1)

	// High-risk emergence should reduce overall coherence
	highRisk := root.Attributes["high_risk_emergence"].(int)
	if highRisk > 0 {
		coherence := graph.Metrics.CoherenceScore
		assert.Less(t, coherence, 0.8)
	}
}
