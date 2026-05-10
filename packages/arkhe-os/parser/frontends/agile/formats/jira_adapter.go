// parser/frontends/agile/formats/jira_adapter.go
package formats

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"arkhe/parser/frontends/agile/models"
)

// JiraAdapter parseia exports JSON do Jira (REST API ou CSV convertido)
type JiraAdapter struct{}

func NewJiraAdapter() *JiraAdapter {
	return &JiraAdapter{}
}

func (a *JiraAdapter) Parse(source []byte, filename string) (*ParsedProject, error) {
	// Detectar formato: JSON (REST API) ou CSV
	if strings.HasSuffix(filename, ".json") {
		return a.parseJSON(source)
	}
	return nil, fmt.Errorf("unsupported file format")
}

// JiraIssue representa um issue do Jira no formato REST API
type JiraIssue struct {
	ID          string            `json:"id"`
	Key         string            `json:"key"`
	Self        string            `json:"self"`
	Fields      JiraIssueFields   `json:"fields"`
	Changelog   *JiraChangelog    `json:"changelog,omitempty"`
}

type JiraIssueFields struct {
	Summary     string           `json:"summary"`
	Description string           `json:"description"`
	Status      JiraStatus       `json:"status"`
	IssueType   JiraIssueType    `json:"issuetype"`
	Priority    *JiraPriority    `json:"priority"`
	Labels      []string         `json:"labels"`
	Components  []JiraComponent  `json:"components"`
	FixVersions []JiraVersion    `json:"fixVersions"`
	Sprint      *JiraSprint      `json:"sprint"` // Campo customizado do GreenHopper
	EpicLink    string           `json:"epic_link"` // Custom field
	Created     string           `json:"created"`
	Updated     string           `json:"updated"`
	Resolved    string           `json:"resolutiondate"`
	TimeTracking *JiraTimeTracking `json:"timetracking"`
}

type JiraStatus struct {
	Name   string `json:"name"`
	ID     string `json:"id"`
	StatusCategory struct {
		Key string `json:"key"` // "new", "indeterminate", "done"
	} `json:"statusCategory"`
}

type JiraIssueType struct {
	Name string `json:"name"`
}

type JiraPriority struct {
	Name string `json:"name"`
}

type JiraComponent struct {
	Name string `json:"name"`
}

type JiraVersion struct {
	Name string `json:"name"`
}

type JiraSprint struct {
	Name string `json:"name"`
}

type JiraTimeTracking struct {
	OriginalEstimateSeconds float64 `json:"originalEstimateSeconds"`
	TimeSpentSeconds        float64 `json:"timeSpentSeconds"`
}

type JiraChangelog struct {
	Histories []JiraHistory `json:"histories"`
}

type JiraHistory struct {
	Created string          `json:"created"`
	Items   []JiraChangeItem `json:"items"`
}

type JiraChangeItem struct {
	Field      string `json:"field"`
	FromString string `json:"fromString"`
	String     string `json:"toString"`
}

// parseJSON parseia export JSON do Jira REST API
func (a *JiraAdapter) parseJSON(source []byte) (*ParsedProject, error) {
	// Pode ser um único issue ou uma lista
	var issues []JiraIssue

	// Tentar parsear como array primeiro
	if err := json.Unmarshal(source, &issues); err != nil {
		// Tentar como objeto único
		var single JiraIssue
		if err := json.Unmarshal(source, &single); err != nil {
			return nil, fmt.Errorf("failed to parse Jira JSON: %w", err)
		}
		issues = []JiraIssue{single}
	}

	project := &ParsedProject{
		Name:        "Jira Project",
		Tool:        "jira",
		Items:       make([]models.WorkItem, 0, len(issues)),
		Transitions: make([]models.Transition, 0),
		CFD:         make(models.CumulativeFlowData, 0),
	}

	for _, issue := range issues {
		item := a.convertIssueToWorkItem(issue)
		project.Items = append(project.Items, item)

		// Extrair transições do changelog
		if issue.Changelog != nil {
			transitions := a.extractTransitions(issue.Key, issue.Changelog)
			project.Transitions = append(project.Transitions, transitions...)
		}
	}

	// Gerar CFD a partir das transições
	if len(project.Transitions) > 0 {
		project.CFD = generateCFD(project.Transitions)
	}

	return project, nil
}

func (a *JiraAdapter) convertIssueToWorkItem(issue JiraIssue) models.WorkItem {
	itemType := mapIssueType(issue.Fields.IssueType.Name)

	sprintName := ""
	if issue.Fields.Sprint != nil {
		sprintName = issue.Fields.Sprint.Name
	}
	priorityName := ""
	if issue.Fields.Priority != nil {
		priorityName = issue.Fields.Priority.Name
	}

	return models.WorkItem{
		ID:          issue.ID,
		Key:         issue.Key,
		Title:       issue.Fields.Summary,
		Description: issue.Fields.Description,
		Type:        itemType,
		Status:      normalizeStatus(issue.Fields.Status.Name),
		Priority:    priorityName,
		Labels:      issue.Fields.Labels,
		CreatedAt:   parseTime(issue.Fields.Created),
		UpdatedAt:   parseTime(issue.Fields.Updated),
		ResolvedAt:  parseTime(issue.Fields.Resolved),
		Epic:        issue.Fields.EpicLink,
		Sprint:      sprintName,
		TimeEstimate: func() float64 {
			if issue.Fields.TimeTracking != nil {
				return issue.Fields.TimeTracking.OriginalEstimateSeconds / 3600.0
			}
			return 0
		}(),
		TimeSpent: func() float64 {
			if issue.Fields.TimeTracking != nil {
				return issue.Fields.TimeTracking.TimeSpentSeconds / 3600.0
			}
			return 0
		}(),
	}
}

func (a *JiraAdapter) extractTransitions(issueKey string, changelog *JiraChangelog) []models.Transition {
	var transitions []models.Transition

	for _, history := range changelog.Histories {
		for _, item := range history.Items {
			if item.Field == "status" {
				transitions = append(transitions, models.Transition{
					IssueKey:    issueKey,
					FromStatus:  normalizeStatus(item.FromString),
					ToStatus:    normalizeStatus(item.String),
					Timestamp:   parseTime(history.Created),
					Actor:       "", // Pode ser extraído se disponível
				})
			}
		}
	}

	return transitions
}

// normalizeStatus mapeia statuses do Jira para estados canônicos
func normalizeStatus(status string) string {
	status = strings.ToLower(status)
	switch {
	case strings.Contains(status, "backlog"), strings.Contains(status, "to do"), strings.Contains(status, "new"):
		return "Backlog"
	case strings.Contains(status, "progress"), strings.Contains(status, "in progress"), strings.Contains(status, "doing"):
		return "In Progress"
	case strings.Contains(status, "review"), strings.Contains(status, "qa"), strings.Contains(status, "testing"):
		return "Review"
	case strings.Contains(status, "done"), strings.Contains(status, "closed"), strings.Contains(status, "released"):
		return "Done"
	case strings.Contains(status, "blocked"), strings.Contains(status, "waiting"):
		return "Blocked"
	default:
		return "Other"
	}
}

// mapIssueType mapeia tipos de issue do Jira
func mapIssueType(issueType string) models.WorkItemType {
	switch strings.ToLower(issueType) {
	case "epic":
		return models.TypeEpic
	case "story", "user story":
		return models.TypeStory
	case "task":
		return models.TypeTask
	case "bug":
		return models.TypeBug
	case "sub-task", "subtask":
		return models.TypeSubtask
	case "spike", "research":
		return models.TypeSpike
	default:
		return models.TypeOther
	}
}

// generateCFD gera dados de Cumulative Flow Diagram a partir de transições
func generateCFD(transitions []models.Transition) models.CumulativeFlowData {
	// Agrupar transições por dia e status
	dailyCounts := make(map[string]map[string]int)

	for _, t := range transitions {
		day := t.Timestamp.Format("2006-01-02")
		if dailyCounts[day] == nil {
			dailyCounts[day] = make(map[string]int)
		}
		// Contar itens que entraram em cada status neste dia
		dailyCounts[day][t.ToStatus]++
	}

	// Calcular acumulado por status
	cfd := make(models.CumulativeFlowData, 0)
	cumulative := make(map[string]int)
	statuses := []string{"Backlog", "In Progress", "Review", "Done", "Blocked"}

	// Ordenar dias
	days := make([]string, 0, len(dailyCounts))
	for day := range dailyCounts {
		days = append(days, day)
	}
	// sort.Strings(days) // Implementar ordenação

	for _, day := range days {
		entry := models.CFDEntry{Date: day, Cumulative: make(map[string]int)}
		for _, status := range statuses {
			cumulative[status] += dailyCounts[day][status]
			entry.Cumulative[status] = cumulative[status]
		}
		entry.Total = 0
		for _, count := range cumulative {
			entry.Total += count
		}
		cfd = append(cfd, entry)
	}

	return cfd
}

func parseTime(timeStr string) time.Time {
	if timeStr == "" {
		return time.Time{}
	}
	t, err := time.Parse(time.RFC3339, timeStr)
	if err != nil {
		t, _ = time.Parse("2006-01-02T15:04:05.000-0700", timeStr)
	}
	return t
}
