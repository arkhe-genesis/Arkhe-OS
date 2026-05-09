package formats

import (
	"encoding/json"
	"fmt"
	"strings"
	"gopkg.in/yaml.v3"

	"arkhe/parser/frontends/agi/models"
)

func ParseYAMLSpec(source []byte) (*models.AGISpecification, error) {
	var spec models.AGISpecification
	err := yaml.Unmarshal(source, &spec)
	if err != nil {
		return nil, fmt.Errorf("yaml parse error: %w", err)
	}

	strSource := string(source)
	if strings.Contains(strSource, `architecture_type: "hybrid"`) {
		spec.ArchitectureType = models.TypeHybrid
	} else if strings.Contains(strSource, `architecture_type: "modular"`) {
		spec.ArchitectureType = models.TypeModular
	} else if strings.Contains(strSource, `architecture_type: "neuro_symbolic"`) {
		spec.ArchitectureType = models.TypeNeuroSymbolic
	} else if strings.Contains(strSource, `architecture_type: "emergent"`) {
		spec.ArchitectureType = models.TypeEmergent
	}

	return &spec, nil
}

func ParseJSONSpec(source []byte) (*models.AGISpecification, error) {
	var spec models.AGISpecification
	err := json.Unmarshal(source, &spec)
	if err != nil {
		return nil, fmt.Errorf("json parse error: %w", err)
	}
	return &spec, nil
}

func ParseMarkdownSpec(source []byte) (*models.AGISpecification, error) {
	return &models.AGISpecification{Name: "Markdown Spec Stub"}, nil
}

func ParseCodeWithSpec(source []byte, filename string) (*models.AGISpecification, error) {
	return &models.AGISpecification{Name: "Code Spec Stub"}, nil
}

func ParsePromptSpec(source []byte) (*models.AGISpecification, error) {
	return &models.AGISpecification{Name: "Prompt Spec Stub"}, nil
}

func ExtractCodeModules(source []byte, filename string) ([]models.CodeModule, error) {
	return nil, nil
}

func ExtractPrompts(source []byte) ([]models.PromptSpec, error) {
	return nil, nil
}
