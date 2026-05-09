package tests

import (
	"testing"

	"arkhe/parser/frontends/agile"
	"arkhe/parser/frontends/agile/analyzers"
	"github.com/stretchr/testify/assert"
)

func TestAgileParser_KanbanBoard(t *testing.T) {
	parser := agile.NewAgileParser()
	parser.ToolType = "generic"
	parser.Methodology = "kanban"

	source := []byte(`{
		"board": "Development Board",
		"columns": [
			{"name": "Backlog", "wip_limit": 0, "items": ["STORY-1", "STORY-2"]},
			{"name": "In Progress", "wip_limit": 3, "items": ["STORY-3", "TASK-1"]},
			{"name": "Review", "wip_limit": 2, "items": []},
			{"name": "Done", "wip_limit": 0, "items": ["STORY-0"]}
		],
		"items": [
			{"key": "STORY-0", "type": "story", "status": "Done", "created": "2024-01-01T00:00:00Z", "resolved": "2024-01-05T00:00:00Z"},
			{"key": "STORY-1", "type": "story", "status": "Backlog", "created": "2024-01-10T00:00:00Z"},
			{"key": "STORY-2", "type": "story", "status": "Backlog", "created": "2024-01-11T00:00:00Z"},
			{"key": "STORY-3", "type": "story", "status": "In Progress", "created": "2024-01-08T00:00:00Z"},
			{"key": "TASK-1", "type": "task", "status": "In Progress", "created": "2024-01-12T00:00:00Z", "blocked": true, "blocker_reason": "Waiting on API"}
		],
		"transitions": [
			{"issue": "STORY-0", "from": "Backlog", "to": "In Progress", "timestamp": "2024-01-02T10:00:00Z"},
			{"issue": "STORY-0", "from": "In Progress", "to": "Review", "timestamp": "2024-01-04T14:00:00Z"},
			{"issue": "STORY-0", "from": "Review", "to": "Done", "timestamp": "2024-01-05T16:00:00Z"}
		]
	}`)

	graph, err := parser.Parse(source, "kanban.json", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)

	assert.GreaterOrEqual(t, graph.Metrics.CoherenceScore, 0.0)
	assert.LessOrEqual(t, graph.Metrics.CoherenceScore, 1.0)

	root := graph.Nodes[graph.RootNodes[0]]
	assert.Equal(t, "kanban", root.Attributes["methodology"])
	assert.Equal(t, 5, root.Attributes["total_items"])
	assert.Equal(t, 1, root.Attributes["completed_items"])
	assert.Greater(t, root.Attributes["flow_efficiency"], 0.0)
}

func TestAgileParser_SprintCoherence(t *testing.T) {
	parser := agile.NewAgileParser()
	parser.ToolType = "generic"
	parser.Methodology = "scrum"

	source := []byte(`{
		"sprints": [{
			"name": "Sprint 42",
			"goal": "Implement user authentication",
			"start_date": "2024-02-01T00:00:00Z",
			"end_date": "2024-02-14T00:00:00Z",
			"planned_items": ["STORY-10", "STORY-11", "TASK-5"],
			"completed_items": ["STORY-10", "TASK-5"],
			"added_items": ["BUG-3"],
			"carry_over_items": ["STORY-11"]
		}, { "name": "Sprint 40", "velocity": 13, "completed_count": 5, "planned_count": 6 },
		{ "name": "Sprint 41", "velocity": 15, "completed_count": 6, "planned_count": 6 },
		{ "name": "Sprint 42", "velocity": 12, "completed_count": 5, "planned_count": 5 }
		],
		"items": [
			{"key": "STORY-10", "type": "story", "status": "Done", "estimate": 5, "spent": 6},
			{"key": "STORY-11", "type": "story", "status": "In Progress", "estimate": 8, "spent": 4},
			{"key": "TASK-5", "type": "task", "status": "Done", "estimate": 3, "spent": 2},
			{"key": "BUG-3", "type": "bug", "status": "Done", "estimate": 2, "spent": 3}
		]
	}`)

	graph, err := parser.Parse(source, "sprint.json", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	assert.Equal(t, "scrum", root.Attributes["methodology"])
	assert.Greater(t, root.Attributes["velocity_stability"], 0.8)
}

func TestAgileParser_BottleneckDetection(t *testing.T) {
	parser := agile.NewAgileParser()
	parser.ToolType = "generic"
	parser.Methodology = "kanban"
	parser.DetectBottlenecks = true

	source := []byte(`{
		"cfd": [
			{"date": "2024-03-01", "cumulative": {"Backlog": 10, "In Progress": 3, "Review": 2, "Done": 5}},
			{"date": "2024-03-02", "cumulative": {"Backlog": 9, "In Progress": 4, "Review": 2, "Done": 6}},
			{"date": "2024-03-03", "cumulative": {"Backlog": 8, "In Progress": 5, "Review": 3, "Done": 6}},
			{"date": "2024-03-04", "cumulative": {"Backlog": 7, "In Progress": 6, "Review": 5, "Done": 6}},
			{"date": "2024-03-05", "cumulative": {"Backlog": 6, "In Progress": 7, "Review": 8, "Done": 6}},
			{"date": "2024-03-06", "cumulative": {"Backlog": 5, "In Progress": 8, "Review": 11, "Done": 6}},
			{"date": "2024-03-07", "cumulative": {"Backlog": 4, "In Progress": 8, "Review": 13, "Done": 7}}
		]
	}`)

	graph, err := parser.Parse(source, "cfd.json", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	bottleneckCount := root.Attributes["bottleneck_count"].(int)
	assert.GreaterOrEqual(t, bottleneckCount, 1)

	coherence := graph.Metrics.CoherenceScore
	assert.Less(t, coherence, 0.95)
}

func TestAgileParser_RetroSentiment(t *testing.T) {
	parser := agile.NewAgileParser()
	parser.ToolType = "generic"
	parser.AnalyzeRetros = true

	source := []byte(`{
		"retrospectives": [
			{
				"sprint": "Sprint 40",
				"went_well": ["Great collaboration", "Fast CI pipeline"],
				"to_improve": ["Too many meetings", "Unclear requirements"],
				"action_items": ["Reduce meeting time", "Improve story refinement"],
				"sentiment_votes": {"happy": 4, "neutral": 2, "sad": 1}
			}
		]
	}`)

	graph, err := parser.Parse(source, "retro.json", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	sentiment := root.Attributes["retro_sentiment"].(analyzers.RetroSentiment)
	score := sentiment.Score
	assert.GreaterOrEqual(t, score, -1.0)
	assert.LessOrEqual(t, score, 1.0)

	teamHealth := root.Attributes["team_health_factor"].(float64)
	assert.Greater(t, teamHealth, 0.2)
}
