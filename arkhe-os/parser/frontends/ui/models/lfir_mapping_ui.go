// parser/frontends/ui/models/lfir_mapping_ui.go
package models

import (
	"fmt"
    "strings"
	"arkhe/parser/lfir"
)

// MapUISpecToLFIR maps a UISpecification to an LFIRGraph for UI coherence.
func MapUISpecToLFIR(spec *UISpecification) *lfir.LFIRGraph {
	graph := lfir.NewLFIRGraph()

	// Root Node
	root := lfir.NewLFIRNode(lfir.LFIRNodeTypeModule, fmt.Sprintf("ui_%s", spec.Name), "ui")
	root.Attributes["name"] = spec.Name
	root.Attributes["version"] = spec.Version
	root.Attributes["rule_count"] = len(spec.Rules)
	root.Attributes["token_count"] = len(spec.DesignTokens)
	graph.AddNode(root)

	// Metrics Node
	metricsNode := lfir.NewLFIRNode(lfir.LFIRNodeTypeMetric, "ui_metrics", "ui")
	metricsNode.Attributes["variable_consistency"] = spec.Metrics.VariableConsistency
	metricsNode.Attributes["specificity_consistency"] = spec.Metrics.SpecificityConsistency
	metricsNode.Attributes["accessibility_score"] = spec.Metrics.AccessibilityScore
	metricsNode.Attributes["maintainability"] = spec.Metrics.Maintainability
	metricsNode.Attributes["overall_coherence"] = spec.Metrics.Overall
	graph.AddNode(metricsNode)
	graph.Link(root.ID, metricsNode.ID)

	// Design Tokens Nodes
	for token, value := range spec.DesignTokens {
		tokenNode := lfir.NewLFIRNode(lfir.LFIRNodeTypeVariable, fmt.Sprintf("token_%s", token), "ui")
		tokenNode.Attributes["name"] = token
		tokenNode.Attributes["value"] = value
		graph.AddNode(tokenNode)
		graph.Link(root.ID, tokenNode.ID)
	}

	// Rule Nodes
	for _, rule := range spec.Rules {
		ruleNode := lfir.NewLFIRNode(lfir.LFIRNodeTypeRule, fmt.Sprintf("rule_%s", sanitizeSelector(rule.Selector)), "ui")
		ruleNode.Attributes["selector"] = rule.Selector
		ruleNode.Attributes["specificity"] = rule.Specificity

		// Link to variables used
		for _, val := range rule.Properties {
			if strings.Contains(val, "var(--") {
				// Extract variable name: var(--name)
				// simplified extraction
				if strings.Contains(val, "(") && strings.Contains(val, ")") {
					start := strings.Index(val, "(") + 5 // len("var(--")
					end := strings.Index(val, ")")
					if start > 4 && end > start {
						varName := "var(" + val[start:end] + ")" // rough approximation
						// In a real parser, we'd link to the specific token node ID
                        _ = varName
					}
				}
			}
		}

		graph.AddNode(ruleNode)
		graph.Link(root.ID, ruleNode.ID)
	}

	// Alerts for low coherence
	if spec.Metrics.Overall < 0.6 {
		alert := lfir.NewLFIRNode(lfir.LFIRNodeTypeAlert, "ui_low_coherence", "ui")
		alert.Attributes["score"] = spec.Metrics.Overall
		alert.Attributes["type"] = "low_ui_coherence"
		graph.AddNode(alert)
		graph.Link(root.ID, alert.ID)
	}

	return graph
}

func sanitizeSelector(sel string) string {
	res := strings.ReplaceAll(sel, " ", "_")
	res = strings.ReplaceAll(res, "#", "id_")
	res = strings.ReplaceAll(res, ".", "class_")
	res = strings.ReplaceAll(res, ":", "pseudo_")
	return res
}