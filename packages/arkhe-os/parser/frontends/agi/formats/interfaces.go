// parser/frontends/agi/formats/interfaces.go
package formats

import "arkhe/parser/frontends/agi/models"

type FrameworkAdapter interface {
	Adapt(spec *models.AGISpecification) *models.AGISpecification
}
