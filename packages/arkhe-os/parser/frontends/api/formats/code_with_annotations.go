package formats

import (
	"arkhe/parser/frontends/api/models"
    "arkhe/parser/frontends/api/formats/framework_adapters"
)

type FrameworkAdapter interface {
    Adapt(spec *models.APISpecification) *models.APISpecification
}

func ParseCodeWithAnnotations(source []byte, filename string, framework string) (*models.APISpecification, error) {
    return &models.APISpecification{}, nil
}

func NewExpressAdapter() FrameworkAdapter { return framework_adapters.NewExpressAdapter() }
func NewSpringAdapter() FrameworkAdapter { return framework_adapters.NewSpringAdapter() }
func NewFastAPIAdapter() FrameworkAdapter { return framework_adapters.NewFastAPIAdapter() }
func NewGenericAdapter() FrameworkAdapter { return framework_adapters.NewGenericAdapter() }
