package formats

import (
	"encoding/json"
	"fmt"

	"arkhe/parser/frontends/agile/models"
)

type AzureAdapter struct{}

func NewAzureAdapter() *AzureAdapter {
	return &AzureAdapter{}
}

type AzureExport struct {
	Count int             `json:"count"`
	Value []AzureWorkItem `json:"value"`
}

type AzureWorkItem struct {
	ID     int             `json:"id"`
	Rev    int             `json:"rev"`
	Fields AzureFields     `json:"fields"`
}

type AzureFields struct {
	Title        string `json:"System.Title"`
	State        string `json:"System.State"`
	WorkItemType string `json:"System.WorkItemType"`
	CreatedDate  string `json:"System.CreatedDate"`
	ChangedDate  string `json:"System.ChangedDate"`
}

func (a *AzureAdapter) Parse(source []byte, filename string) (*ParsedProject, error) {
	var export AzureExport
	if err := json.Unmarshal(source, &export); err != nil {
		return nil, fmt.Errorf("failed to parse Azure JSON: %w", err)
	}

	project := &ParsedProject{
		Name:        "Azure DevOps Project",
		Tool:        "azure",
		Items:       make([]models.WorkItem, 0),
		Transitions: make([]models.Transition, 0),
		CFD:         make(models.CumulativeFlowData, 0),
	}

	for _, item := range export.Value {
		key := fmt.Sprintf("AB-%d", item.ID)

		itemType := models.TypeTask
		switch item.Fields.WorkItemType {
		case "Bug":
			itemType = models.TypeBug
		case "User Story":
			itemType = models.TypeStory
		case "Epic":
			itemType = models.TypeEpic
		case "Feature":
			itemType = models.TypeEpic
		}

		project.Items = append(project.Items, models.WorkItem{
			ID:        key,
			Key:       key,
			Title:     item.Fields.Title,
			Type:      itemType,
			Status:    normalizeStatus(item.Fields.State),
			CreatedAt: parseTime(item.Fields.CreatedDate),
			UpdatedAt: parseTime(item.Fields.ChangedDate),
		})
	}

	return project, nil
}
