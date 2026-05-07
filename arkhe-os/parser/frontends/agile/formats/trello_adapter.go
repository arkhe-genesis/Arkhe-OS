package formats

import (
	"encoding/json"
	"fmt"
	"strings"

	"arkhe/parser/frontends/agile/models"
)

type TrelloAdapter struct{}

func NewTrelloAdapter() *TrelloAdapter {
	return &TrelloAdapter{}
}

type TrelloExport struct {
	Name    string         `json:"name"`
	Lists   []TrelloList   `json:"lists"`
	Cards   []TrelloCard   `json:"cards"`
	Actions []TrelloAction `json:"actions"`
}

type TrelloList struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

type TrelloCard struct {
	ID     string       `json:"id"`
	Name   string       `json:"name"`
	Desc   string       `json:"desc"`
	IDList string       `json:"idList"`
	Closed bool         `json:"closed"`
	Labels []TrelloLabel `json:"labels"`
}

type TrelloLabel struct {
	Name string `json:"name"`
}

type TrelloAction struct {
	Type string       `json:"type"`
	Date string       `json:"date"`
	Data TrelloActionData `json:"data"`
}

type TrelloActionData struct {
	Card TrelloActionCard `json:"card"`
	ListBefore *TrelloList `json:"listBefore,omitempty"`
	ListAfter  *TrelloList `json:"listAfter,omitempty"`
}

type TrelloActionCard struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

func (a *TrelloAdapter) Parse(source []byte, filename string) (*ParsedProject, error) {
	var export TrelloExport
	if err := json.Unmarshal(source, &export); err != nil {
		return nil, fmt.Errorf("failed to parse Trello JSON: %w", err)
	}

	project := &ParsedProject{
		Name:        export.Name,
		Tool:        "trello",
		Items:       make([]models.WorkItem, 0),
		Transitions: make([]models.Transition, 0),
		Columns:     make([]models.Column, 0),
		CFD:         make(models.CumulativeFlowData, 0),
	}

	listMap := make(map[string]string)
	for _, l := range export.Lists {
		listMap[l.ID] = l.Name
		project.Columns = append(project.Columns, models.Column{
			Name: l.Name,
		})
	}

	for _, c := range export.Cards {
		status := listMap[c.IDList]
		if c.Closed {
			status = "Done"
		}
		status = normalizeStatus(status)

		labels := make([]string, 0)
		for _, l := range c.Labels {
			labels = append(labels, l.Name)
		}

		itemType := models.TypeTask
		for _, l := range labels {
			if strings.ToLower(l) == "bug" {
				itemType = models.TypeBug
			} else if strings.ToLower(l) == "story" {
				itemType = models.TypeStory
			}
		}

		project.Items = append(project.Items, models.WorkItem{
			ID:          c.ID,
			Key:         c.ID,
			Title:       c.Name,
			Description: c.Desc,
			Type:        itemType,
			Status:      status,
			Labels:      labels,
		})
	}

	for _, action := range export.Actions {
		if action.Type == "updateCard" && action.Data.ListBefore != nil && action.Data.ListAfter != nil {
			project.Transitions = append(project.Transitions, models.Transition{
				IssueKey:   action.Data.Card.ID,
				FromStatus: normalizeStatus(action.Data.ListBefore.Name),
				ToStatus:   normalizeStatus(action.Data.ListAfter.Name),
				Timestamp:  parseTime(action.Date),
			})
		}
	}

	if len(project.Transitions) > 0 {
		project.CFD = generateCFD(project.Transitions)
	}

	return project, nil
}
