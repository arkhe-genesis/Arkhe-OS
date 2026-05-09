package models

import "time"

type AgileProject struct {
	Name           string
	Methodology    string
	Items          []WorkItem
	Transitions    []Transition
	CFD            CumulativeFlowData
	Sprints        []Sprint
	Retrospectives []Retrospective
	WIPLimits      map[string]int
	Columns        []Column
}

type WorkItemType string

const (
	TypeEpic    WorkItemType = "epic"
	TypeStory   WorkItemType = "story"
	TypeTask    WorkItemType = "task"
	TypeBug     WorkItemType = "bug"
	TypeSubtask WorkItemType = "subtask"
	TypeSpike   WorkItemType = "spike"
	TypeOther   WorkItemType = "other"
)

type WorkItem struct {
	ID              string
	Key             string
	Title           string
	Description     string
	Type            WorkItemType
	Status          string
	Priority        string
	Labels          []string
	CreatedAt       time.Time
	UpdatedAt       time.Time
	ResolvedAt      time.Time
	Epic            string
	Sprint          string
	TimeEstimate    float64
	TimeSpent       float64
	ChildIDs        []string
	Blocked         bool
	BlockerReason   string
	BlockedSince    time.Time
	BlockerSeverity float64
}

type Transition struct {
	IssueKey      string
	FromStatus    string
	ToStatus      string
	Timestamp     time.Time
	Actor         string
	DurationHours float64
}

type CFDEntry struct {
	Date       string
	Cumulative map[string]int
	Total      int
}

type CumulativeFlowData []CFDEntry

type Sprint struct {
	Name           string
	Goal           string
	StartDate      time.Time
	EndDate        time.Time
	PlannedItemIDs []string
	ItemIDs        []string
	PlannedCount   int
	CompletedCount int
	AddedCount     int
	CarryOverCount int
	Velocity       float64
}

type Column struct {
	Name             string
	WIPLimit         int
	CurrentCount     int
	AvgCycleTimeDays float64
	ItemIDs          []string
}

type Retrospective struct {
	Sprint         string                 `json:"sprint"`
	WentWell       []string               `json:"went_well"`
	ToImprove      []string               `json:"to_improve"`
	ActionItems    []string               `json:"action_items"`
	SentimentVotes map[string]int         `json:"sentiment_votes"`
}
