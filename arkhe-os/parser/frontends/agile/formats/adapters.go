package formats

import (
	"arkhe/parser/frontends/agile/models"
)

type ToolAdapter interface {
	Parse(source []byte, filename string) (*ParsedProject, error)
}

type ParsedProject struct {
	Name        string
	Tool        string
	Items       []models.WorkItem
	Transitions []models.Transition
	CFD         models.CumulativeFlowData
	Sprints     []models.Sprint
	Retros      []models.Retrospective
	WIPLimits   map[string]int
	Columns     []models.Column
}
