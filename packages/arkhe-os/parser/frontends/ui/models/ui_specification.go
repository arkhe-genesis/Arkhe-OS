// parser/frontends/ui/models/ui_specification.go
package models

// UISpecification represents the canonical model for a CSS/Stylesheet specification.
type UISpecification struct {
	Name         string            `json:"name"`
	Version      string            `json:"version"`
	Description  string            `json:"description,omitempty"`
	DesignTokens map[string]string `json:"design_tokens"` // CSS Variables
	Rules        []UIRule          `json:"rules"`
	Metrics      UICoherenceMetrics `json:"metrics"`
}

// UIRule represents a CSS rule set.
type UIRule struct {
	Selector      string            `json:"selector"`
	Properties    map[string]string `json:"properties"`
	Specificity   int               `json:"specificity"`
	Accessibility AccessibilityHints `json:"accessibility,omitempty"`
}

// AccessibilityHints tracks basic accessibility patterns.
type AccessibilityHints struct {
	HasFocusState   bool `json:"has_focus_state"`
	HasActiveState  bool `json:"has_active_state"`
	HasContrastDef  bool `json:"has_contrast_def"`
}

// UICoherenceMetrics holds the calculated coherence scores for the stylesheet.
type UICoherenceMetrics struct {
	VariableConsistency    float64 `json:"variable_consistency"`    // 0.0-1.0, usage of design tokens
	SpecificityConsistency float64 `json:"specificity_consistency"` // 0.0-1.0, low variance is good
	AccessibilityScore     float64 `json:"accessibility_score"`     // 0.0-1.0, focus states etc.
	Maintainability        float64 `json:"maintainability"`         // 0.0-1.0, complexity management
	Overall                float64 `json:"overall"`                 // Weighted average
}
