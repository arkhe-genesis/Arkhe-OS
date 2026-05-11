package formats

import (
	"encoding/json"
	"strings"

	"arkhe/parser/frontends/agile/models"
)

type GenericAdapter struct {
	filename string
}

func AutoDetectAdapter(filename string) ToolAdapter {
	return &GenericAdapter{filename: filename}
}

type GenericData struct {
	Board       string                 `json:"board"`
	Columns     []GenericColumn        `json:"columns"`
	Items       []GenericItem          `json:"items"`
	Transitions []GenericTransition    `json:"transitions"`
	Sprints     []GenericSprint        `json:"sprints"`
	CFD         []models.CFDEntry      `json:"cfd"`
	Retros      []models.Retrospective `json:"retrospectives"`
}

type GenericColumn struct {
	Name     string   `json:"name"`
	WIPLimit int      `json:"wip_limit"`
	Items    []string `json:"items"`
}

type GenericItem struct {
	Key           string  `json:"key"`
	Type          string  `json:"type"`
	Status        string  `json:"status"`
	Created       string  `json:"created"`
	Resolved      string  `json:"resolved"`
	Estimate      float64 `json:"estimate"`
	Spent         float64 `json:"spent"`
	Blocked       bool    `json:"blocked"`
	BlockerReason string  `json:"blocker_reason"`
}

type GenericTransition struct {
	Issue     string `json:"issue"`
	From      string `json:"from"`
	To        string `json:"to"`
	Timestamp string `json:"timestamp"`
}

type GenericSprint struct {
	Name           string   `json:"name"`
	Goal           string   `json:"goal"`
	StartDate      string   `json:"start_date"`
	EndDate        string   `json:"end_date"`
	PlannedItems   []string `json:"planned_items"`
	CompletedItems []string `json:"completed_items"`
	AddedItems     []string `json:"added_items"`
	CarryOverItems []string `json:"carry_over_items"`
	Velocity       float64  `json:"velocity"`
	PlannedCount   int      `json:"planned_count"`
	CompletedCount int      `json:"completed_count"`
}

func (a *GenericAdapter) Parse(source []byte, filename string) (*ParsedProject, error) {
	var data GenericData
	if err := json.Unmarshal(source, &data); err != nil {
		return nil, err
	}

	project := &ParsedProject{
		Name:      data.Board,
		Tool:      "generic",
		Items:     make([]models.WorkItem, 0),
		CFD:       data.CFD,
		Retros:    data.Retros,
		Columns:   make([]models.Column, 0),
		Sprints:   make([]models.Sprint, 0),
		Transitions: make([]models.Transition, 0),
	}

	for _, item := range data.Items {
		project.Items = append(project.Items, models.WorkItem{
			ID:            item.Key,
			Key:           item.Key,
			Type:          models.WorkItemType(strings.ToLower(item.Type)),
			Status:        item.Status,
			CreatedAt:     parseTime(item.Created),
			ResolvedAt:    parseTime(item.Resolved),
			TimeEstimate:  item.Estimate,
			TimeSpent:     item.Spent,
			Blocked:       item.Blocked,
			BlockerReason: item.BlockerReason,
		})
	}

	for _, col := range data.Columns {
		project.Columns = append(project.Columns, models.Column{
			Name:     col.Name,
			WIPLimit: col.WIPLimit,
			ItemIDs:  col.Items,
		})
	}

	for _, trans := range data.Transitions {
		project.Transitions = append(project.Transitions, models.Transition{
			IssueKey:   trans.Issue,
			FromStatus: trans.From,
			ToStatus:   trans.To,
			Timestamp:  parseTime(trans.Timestamp),
		})
	}

	for _, sprint := range data.Sprints {

		planned := sprint.PlannedCount
		if planned == 0 {
			planned = len(sprint.PlannedItems)
		}
		completed := sprint.CompletedCount
		if completed == 0 {
			completed = len(sprint.CompletedItems)
		}

		project.Sprints = append(project.Sprints, models.Sprint{
			Name:           sprint.Name,
			Goal:           sprint.Goal,
			StartDate:      parseTime(sprint.StartDate),
			EndDate:        parseTime(sprint.EndDate),
			PlannedItemIDs: sprint.PlannedItems,
			ItemIDs:        append(sprint.PlannedItems, sprint.AddedItems...),
			PlannedCount:   planned,
			CompletedCount: completed,
			AddedCount:     len(sprint.AddedItems),
			CarryOverCount: len(sprint.CarryOverItems),
			Velocity:       sprint.Velocity,
		})
	}

	return project, nil
}
