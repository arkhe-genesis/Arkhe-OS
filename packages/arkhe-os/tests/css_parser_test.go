package tests

import (
	"testing"
	"arkhe/parser/frontends/ui/formats"
)

func TestCSSParser(t *testing.T) {
	css := []byte(`
:root {
	--primary-color: #007bff;
	--spacing-unit: 8px;
}

body {
	font-family: var(--font-main);
	color: #333;
}

.card {
	background: #fff;
	padding: calc(var(--spacing-unit) * 2);
}

button:focus {
	background-color: var(--primary-color);
}
`)

	spec, err := formats.ParseCSS(css)
	if err != nil {
		t.Fatalf("Failed to parse CSS: %v", err)
	}

	if len(spec.DesignTokens) != 2 {
		t.Errorf("Expected 2 design tokens, got %d", len(spec.DesignTokens))
	}

	if val, ok := spec.DesignTokens["--primary-color"]; !ok || val != "#007bff" {
		t.Errorf("Expected --primary-color to be #007bff, got %v", val)
	}

	if len(spec.Rules) != 4 {
		t.Errorf("Expected 4 rules, got %d", len(spec.Rules))
	}

	// Test metrics broadly
	if spec.Metrics.VariableConsistency <= 0.0 {
		t.Errorf("VariableConsistency should be > 0")
	}
}
