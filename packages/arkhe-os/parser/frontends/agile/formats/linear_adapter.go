package formats

import (
	"encoding/json"
	"fmt"

	"arkhe/parser/frontends/agile/models"
)

type LinearAdapter struct{}

func NewLinearAdapter() *LinearAdapter {
	return &LinearAdapter{}
}

type LinearExport struct {
	Data LinearData `json:"data"`
}

type LinearData struct {
	Issues LinearIssues `json:"issues"`
}

type LinearIssues struct {
	Nodes []LinearNode `json:"nodes"`
}

type LinearNode struct {
	ID        string       `json:"id"`
	Identifier string       `json:"identifier"`
	Title     string       `json:"title"`
	State     LinearState  `json:"state"`
	CreatedAt string       `json:"createdAt"`
	UpdatedAt string       `json:"updatedAt"`
	Estimate  float64      `json:"estimate"`
}

type LinearState struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

func (a *LinearAdapter) Parse(source []byte, filename string) (*ParsedProject, error) {
	var export LinearExport
	if err := json.Unmarshal(source, &export); err != nil {
		return nil, fmt.Errorf("failed to parse Linear JSON: %w", err)
	}

	project := &ParsedProject{
		Name:        "Linear Project",
		Tool:        "linear",
		Items:       make([]models.WorkItem, 0),
		Transitions: make([]models.Transition, 0),
		CFD:         make(models.CumulativeFlowData, 0),
	}

	for _, item := range export.Data.Issues.Nodes {
		status := "Backlog"
		switch item.State.Type {
		case "backlog", "unstarted":
			status = "Backlog"
		case "started":
			status = "In Progress"
		case "completed", "canceled":
			status = "Done"
		}

		project.Items = append(project.Items, models.WorkItem{
			ID:           item.ID,
			Key:          item.Identifier,
			Title:        item.Title,
			Type:         models.TypeTask,
			Status:       status,
			CreatedAt:    parseTime(item.CreatedAt),
			UpdatedAt:    parseTime(item.UpdatedAt),
			TimeEstimate: item.Estimate,
		})
	}

	return project, nil
}
