package formats

import (
	"regexp"
	"strings"

	"arkhe/parser/frontends/ui/models"
)

// ParseCSS parses a CSS stylesheet into a canonical UISpecification model.
func ParseCSS(source []byte) (*models.UISpecification, error) {
	content := string(source)
	spec := &models.UISpecification{
		Name:    "Stylesheet",
		Version: "1.0",
		DesignTokens: make(map[string]string),
		Rules:   make([]models.UIRule, 0),
	}

	// 1. Extract Variables (Design Tokens)
	// Regex: --variable-name: value;
	varRe := regexp.MustCompile(`(--[\w-]+)\s*:\s*([^;]+);`)
	for _, match := range varRe.FindAllStringSubmatch(content, -1) {
		name := match[1]
		value := strings.TrimSpace(match[2])
		spec.DesignTokens[name] = value
	}

	// 2. Extract Rules
	// Regex: selector { properties } (simplified, doesn't handle nested media queries perfectly in one pass)
	ruleRe := regexp.MustCompile(`([^{]+)\{([^}]+)\}`)
	matches := ruleRe.FindAllStringSubmatch(content, -1)

	for _, match := range matches {
		selector := strings.TrimSpace(match[1])
		block := match[2]

		// Skip @rules (media, keyframes, etc.) for now, or parse them separately
		if strings.HasPrefix(selector, "@") {
			continue
		}

		// Parse properties
		props := make(map[string]string)
		propRe := regexp.MustCompile(`([\w-]+)\s*:\s*([^;]+);`)
		propMatches := propRe.FindAllStringSubmatch(block, -1)
		for _, pMatch := range propMatches {
			props[strings.TrimSpace(pMatch[1])] = strings.TrimSpace(pMatch[2])
		}

		rule := models.UIRule{
			Selector:   selector,
			Properties: props,
			Specificity: calculateSpecificity(selector),
		}

		// Check for Accessibility hints
		rule.Accessibility = checkAccessibilityHints(props, selector)

		spec.Rules = append(spec.Rules, rule)
	}

	// 3. Compute Coherence Metrics
	spec.Metrics = computeCSSCoherence(spec)

	return spec, nil
}

// calculateSpecificity calculates CSS specificity score (a, b, c) -> int
// a: IDs, b: classes/attributes/pseudo-classes, c: elements/pseudo-elements
func calculateSpecificity(selector string) int {
	selectors := strings.Split(selector, ",")
	maxA, maxB, maxC := 0, 0, 0

	for _, s := range selectors {
		s = strings.TrimSpace(s)
		// Count IDs
		idMatches := regexp.MustCompile(`#`).FindAllString(s, -1)
		a := len(idMatches)

		// Count Classes, Attributes, Pseudo-classes
		classMatches := regexp.MustCompile(`\.`).FindAllString(s, -1)
		attrMatches := regexp.MustCompile(`\[[\w-]+`).FindAllString(s, -1)

		// Go's regexp doesn't support negative lookahead (?!), so we need a workaround
		// We want to match :pseudo-class but NOT ::pseudo-element
		allColons := regexp.MustCompile(`:{1,2}[\w-]+`).FindAllString(s, -1)
		pseudoClassCount := 0
		for _, match := range allColons {
			if strings.HasPrefix(match, ":") && !strings.HasPrefix(match, "::") {
				pseudoClassCount++
			}
		}

		b := len(classMatches) + len(attrMatches) + pseudoClassCount

		// Count Elements, Pseudo-elements
		// Remove IDs, Classes, Attributes, Pseudo-classes to isolate elements
		temp := s
		temp = regexp.MustCompile(`#[\w-]+`).ReplaceAllString(temp, "")
		temp = regexp.MustCompile(`\.[\w-]+`).ReplaceAllString(temp, "")
		temp = regexp.MustCompile(`\[[\w-]+\]`).ReplaceAllString(temp, "")
		temp = regexp.MustCompile(`::[\w-]+`).ReplaceAllString(temp, "") // pseudo-elements first
		temp = regexp.MustCompile(`:[\w-]+`).ReplaceAllString(temp, "") // pseudo-classes

		// Split by whitespace to get elements
		elements := strings.Fields(temp)
		// Filter out combinators
		elementCount := 0
		for _, e := range elements {
			if e != ">" && e != "+" && e != "~" && e != "" {
				elementCount++
			}
		}
		c := elementCount

		// Compare specificities to find max for this selector group
		if a > maxA || (a == maxA && b > maxB) || (a == maxA && b == maxB && c > maxC) {
			maxA, maxB, maxC = a, b, c
		}
	}

	// Return weighted score: A*100 + B*10 + C
	return maxA*100 + maxB*10 + maxC
}

// checkAccessibilityHints checks for basic accessibility patterns
func checkAccessibilityHints(props map[string]string, selector string) models.AccessibilityHints {
	hints := models.AccessibilityHints{
		HasFocusState: false,
		HasActiveState: false,
	}

	// Check pseudo-classes in selector
	if strings.Contains(selector, ":focus") || strings.Contains(selector, ":focus-visible") {
		hints.HasFocusState = true
	}
	if strings.Contains(selector, ":active") {
		hints.HasActiveState = true
	}

	// Check contrast-related properties
	if _, ok := props["color"]; ok {
		if _, ok2 := props["background-color"]; ok2 {
			hints.HasContrastDef = true
		}
	}

	return hints
}

// computeCSSCoherence calculates the coherence metrics for the stylesheet
func computeCSSCoherence(spec *models.UISpecification) models.UICoherenceMetrics {
	metrics := models.UICoherenceMetrics{}

	totalRules := len(spec.Rules)
	if totalRules == 0 {
		return metrics
	}

	// 1. Variable Usage Consistency
	variableUses := 0
	totalValues := 0
	for _, rule := range spec.Rules {
		for _, val := range rule.Properties {
			totalValues++
			if strings.Contains(val, "var(--") {
				variableUses++
			}
		}
	}
	if totalValues > 0 {
		metrics.VariableConsistency = float64(variableUses) / float64(totalValues)
	}

	// 2. Specificity Variance (Lower variance = Higher coherence)
	specSum := 0.0
	for _, rule := range spec.Rules {
		specSum += float64(rule.Specificity)
	}
	specMean := specSum / float64(totalRules)

	specVariance := 0.0
	for _, rule := range spec.Rules {
		diff := float64(rule.Specificity) - specMean
		specVariance += diff * diff
	}
	specVariance /= float64(totalRules)

	// Map variance to 0-1 score (low variance -> high score)
	// Heuristic: Variance > 1000 is considered chaotic
	metrics.SpecificityConsistency = 1.0 - min(1.0, specVariance/1000.0)

	// 3. Accessibility Score
	a11yCount := 0
	for _, rule := range spec.Rules {
		if rule.Accessibility.HasFocusState {
			a11yCount++
		}
	}
	// Heuristic: % of interactive-looking selectors that have focus states
	interactiveCount := 0
	for _, rule := range spec.Rules {
		if strings.Contains(rule.Selector, "button") || strings.Contains(rule.Selector, "a") || strings.Contains(rule.Selector, "input") {
			interactiveCount++
		}
	}
	if interactiveCount > 0 {
		metrics.AccessibilityScore = float64(a11yCount) / float64(interactiveCount)
	} else {
		metrics.AccessibilityScore = 1.0 // No interactive elements found
	}

	// 4. Maintainability (Nesting Depth - approximated by selector complexity)
	// Heuristic: Specificity > 30 implies deep nesting or over-qualification
	complexCount := 0
	for _, rule := range spec.Rules {
		if rule.Specificity > 30 {
			complexCount++
		}
	}
	metrics.Maintainability = 1.0 - (float64(complexCount) / float64(totalRules))

	// Overall Coherence
	metrics.Overall = (metrics.VariableConsistency*0.3 + metrics.SpecificityConsistency*0.3 + metrics.AccessibilityScore*0.2 + metrics.Maintainability*0.2)

	return metrics
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
