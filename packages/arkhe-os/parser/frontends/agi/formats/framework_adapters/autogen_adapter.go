// parser/frontends/agi/formats/framework_adapters/autogen_adapter.go
package framework_adapters

import "arkhe/parser/frontends/agi/models"

type AutoGenAdapter struct{}

func NewAutoGenAdapter() *AutoGenAdapter {
	return &AutoGenAdapter{}
}

func (a *AutoGenAdapter) Adapt(spec *models.AGISpecification) *models.AGISpecification {
	return spec
}
