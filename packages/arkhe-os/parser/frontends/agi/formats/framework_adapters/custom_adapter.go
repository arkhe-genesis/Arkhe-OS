// parser/frontends/agi/formats/framework_adapters/custom_adapter.go
package framework_adapters

import "arkhe/parser/frontends/agi/models"

type GenericAdapter struct{}

func NewGenericAdapter() *GenericAdapter {
	return &GenericAdapter{}
}

func (a *GenericAdapter) Adapt(spec *models.AGISpecification) *models.AGISpecification {
	return spec
}
