package formats

import (
	"encoding/json"
	"fmt"

	"arkhe/parser/frontends/agile/models"
)

type GitHubAdapter struct{}

func NewGitHubAdapter() *GitHubAdapter {
	return &GitHubAdapter{}
}

type GitHubExport struct {
	Project GitHubProject `json:"project"`
	Items   []GitHubItem  `json:"items"`
}

type GitHubProject struct {
	Name string `json:"name"`
}

type GitHubItem struct {
	ID        string      `json:"id"`
	Title     string      `json:"title"`
	State     string      `json:"state"`
	Type      string      `json:"type"`
	CreatedAt string      `json:"createdAt"`
	UpdatedAt string      `json:"updatedAt"`
	ClosedAt  string      `json:"closedAt"`
}

func (a *GitHubAdapter) Parse(source []byte, filename string) (*ParsedProject, error) {
	var export GitHubExport
	if err := json.Unmarshal(source, &export); err != nil {
		return nil, fmt.Errorf("failed to parse GitHub JSON: %w", err)
	}

	project := &ParsedProject{
		Name:        export.Project.Name,
		Tool:        "github",
		Items:       make([]models.WorkItem, 0),
		Transitions: make([]models.Transition, 0),
		CFD:         make(models.CumulativeFlowData, 0),
	}

	for _, item := range export.Items {
		itemType := models.TypeTask
		if item.Type == "Issue" {
			itemType = models.TypeStory
		}

		project.Items = append(project.Items, models.WorkItem{
			ID:         item.ID,
			Key:        item.ID,
			Title:      item.Title,
			Type:       itemType,
			Status:     normalizeStatus(item.State),
			CreatedAt:  parseTime(item.CreatedAt),
			UpdatedAt:  parseTime(item.UpdatedAt),
			ResolvedAt: parseTime(item.ClosedAt),
		})
	}

	return project, nil
}
