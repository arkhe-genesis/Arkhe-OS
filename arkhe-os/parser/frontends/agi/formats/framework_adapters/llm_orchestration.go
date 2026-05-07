// parser/frontends/agi/formats/framework_adapters/llm_orchestration.go
package framework_adapters

import "arkhe/parser/frontends/agi/models"

type LLMOrchestrationAdapter struct{}

func NewLLMOrchestrationAdapter() *LLMOrchestrationAdapter {
	return &LLMOrchestrationAdapter{}
}

func (a *LLMOrchestrationAdapter) Adapt(spec *models.AGISpecification) *models.AGISpecification {
	return spec
}
