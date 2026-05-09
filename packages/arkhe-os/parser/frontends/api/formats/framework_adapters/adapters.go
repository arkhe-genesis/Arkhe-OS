package framework_adapters

import (
	"arkhe/parser/frontends/api/models"
)

func NewExpressAdapter() *ExpressAdapter { return &ExpressAdapter{} }
func NewSpringAdapter() *SpringAdapter { return &SpringAdapter{} }
func NewFastAPIAdapter() *FastAPIAdapter { return &FastAPIAdapter{} }
func NewGenericAdapter() *GenericAdapter { return &GenericAdapter{} }

type ExpressAdapter struct{}
func (a *ExpressAdapter) Adapt(spec *models.APISpecification) *models.APISpecification { return spec }

type SpringAdapter struct{}
func (a *SpringAdapter) Adapt(spec *models.APISpecification) *models.APISpecification { return spec }

type FastAPIAdapter struct{}
func (a *FastAPIAdapter) Adapt(spec *models.APISpecification) *models.APISpecification { return spec }

type GenericAdapter struct{}
func (a *GenericAdapter) Adapt(spec *models.APISpecification) *models.APISpecification { return spec }
