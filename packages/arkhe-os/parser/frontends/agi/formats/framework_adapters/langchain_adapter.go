// parser/frontends/agi/formats/framework_adapters/langchain_adapter.go
package framework_adapters

import "arkhe/parser/frontends/agi/models"

type LangChainAdapter struct{}

func NewLangChainAdapter() *LangChainAdapter {
	return &LangChainAdapter{}
}

func (a *LangChainAdapter) Adapt(spec *models.AGISpecification) *models.AGISpecification {
	return spec
}
