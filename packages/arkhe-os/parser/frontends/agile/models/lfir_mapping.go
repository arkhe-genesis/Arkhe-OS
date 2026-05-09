// parser/frontends/agile/models/lfir_mapping.go
package models

import (
	"fmt"

	"arkhe/parser/lfir"
)

// LFIR node types específicos para Agile
const (
	LFIRNodeTypeEpic        lfir.LFIRNodeType = "agile_epic"
	LFIRNodeTypeStory       lfir.LFIRNodeType = "agile_story"
	LFIRNodeTypeTask        lfir.LFIRNodeType = "agile_task"
	LFIRNodeTypeBug         lfir.LFIRNodeType = "agile_bug"
	LFIRNodeTypeSprint      lfir.LFIRNodeType = "agile_sprint"
	LFIRNodeTypeBoard       lfir.LFIRNodeType = "agile_board"
	LFIRNodeTypeColumn      lfir.LFIRNodeType = "agile_column"
	LFIRNodeTypeSwimlane    lfir.LFIRNodeType = "agile_swimlane"
	LFIRNodeTypeTransition  lfir.LFIRNodeType = "agile_transition"
	LFIRNodeTypeBlocker     lfir.LFIRNodeType = "agile_blocker"
	LFIRNodeTypeRetro       lfir.LFIRNodeType = "agile_retrospective"
)

// AgileLFIRBuilder converte modelo Agile interno → grafo LFIR
type AgileLFIRBuilder struct {
	graph        *lfir.LFIRGraph
	rootID       string
	methodology  string
	itemNodeMap  map[string]string // WorkItem.ID → LFIR node ID
}

func NewAgileLFIRBuilder(graph *lfir.LFIRGraph, rootID, methodology string) *AgileLFIRBuilder {
	return &AgileLFIRBuilder{
		graph:       graph,
		rootID:      rootID,
		methodology: methodology,
		itemNodeMap: make(map[string]string),
	}
}

// Build converte projeto ágil para LFIR
func (b *AgileLFIRBuilder) Build(project *AgileProject) error {
	// Criar nó de board/sprint root baseado na metodologia
	if b.methodology == "scrum" {
		for _, sprint := range project.Sprints {
			sprintNode := b.createSprintNode(sprint)
			b.graph.AddNode(sprintNode)
			b.graph.Link(b.rootID, sprintNode.ID)

			// Adicionar itens do sprint
			for _, itemID := range sprint.ItemIDs {
				if item, exists := b.findItem(project.Items, itemID); exists {
					itemNode := b.createWorkItemNode(item)
					b.graph.AddNode(itemNode)
					b.graph.Link(sprintNode.ID, itemNode.ID)
					b.itemNodeMap[item.ID] = itemNode.ID
				}
			}
		}
	} else { // kanban
		boardNode := b.createBoardNode(project.Name)
		b.graph.AddNode(boardNode)
		b.graph.Link(b.rootID, boardNode.ID)

		// Criar columns
		for _, col := range project.Columns {
			colNode := b.createColumnNode(col)
			b.graph.AddNode(colNode)
			b.graph.Link(boardNode.ID, colNode.ID)

			// Adicionar cards na column
			for _, itemID := range col.ItemIDs {
				if item, exists := b.findItem(project.Items, itemID); exists {
					itemNode := b.createWorkItemNode(item)
					b.graph.AddNode(itemNode)
					b.graph.Link(colNode.ID, itemNode.ID)
					b.itemNodeMap[item.ID] = itemNode.ID
				}
			}
		}
	}

	// Adicionar arestas de transição (fluxo de trabalho)
	for _, transition := range project.Transitions {
		if fromNodeID, fromExists := b.itemNodeMap[transition.IssueKey]; fromExists {
			if toNodeID, toExists := b.itemNodeMap[transition.IssueKey]; toExists {
				// Criar nó de transição
				transNode := lfir.NewLFIRNode(LFIRNodeTypeTransition,
					fmt.Sprintf("trans_%s_%d", transition.IssueKey, transition.Timestamp.Unix()),
					"agile")
				transNode.Attributes["from_status"] = transition.FromStatus
				transNode.Attributes["to_status"] = transition.ToStatus
				transNode.Attributes["timestamp"] = transition.Timestamp.Unix()
				transNode.Attributes["duration_hours"] = transition.DurationHours

				b.graph.AddNode(transNode)
				b.graph.Link(fromNodeID, transNode.ID)
				b.graph.Link(transNode.ID, toNodeID)
			}
		}
	}

	// Adicionar epics como agrupadores
	for _, item := range project.Items {
		if item.Type == TypeEpic && item.ID != "" {
			epicNode := b.createWorkItemNode(item)
			b.graph.AddNode(epicNode)
			b.graph.Link(b.rootID, epicNode.ID)
			b.itemNodeMap[item.ID] = epicNode.ID

			// Link child items ao epic
			for _, childID := range item.ChildIDs {
				if childNodeID, exists := b.itemNodeMap[childID]; exists {
					b.graph.Link(epicNode.ID, childNodeID)
				}
			}
		}
	}

	// Adicionar blockers como alertas
	for _, item := range project.Items {
		if item.Blocked && item.BlockerReason != "" {
			blockerNode := lfir.NewLFIRNode(LFIRNodeTypeBlocker,
				fmt.Sprintf("blocker_%s", item.Key), "agile")
			blockerNode.Attributes["issue_key"] = item.Key
			blockerNode.Attributes["reason"] = item.BlockerReason
			blockerNode.Attributes["blocked_since"] = item.BlockedSince.Unix()
			blockerNode.Attributes["severity"] = item.BlockerSeverity

			b.graph.AddNode(blockerNode)
			if itemNodeID, exists := b.itemNodeMap[item.ID]; exists {
				b.graph.Link(itemNodeID, blockerNode.ID)
			}
		}
	}

	return nil
}

func (b *AgileLFIRBuilder) createWorkItemNode(item WorkItem) *lfir.LFIRNode {
	nodeType := lfir.LFIRNodeTypeModule // default
	switch item.Type {
	case TypeEpic:
		nodeType = LFIRNodeTypeEpic
	case TypeStory:
		nodeType = LFIRNodeTypeStory
	case TypeTask:
		nodeType = LFIRNodeTypeTask
	case TypeBug:
		nodeType = LFIRNodeTypeBug
	}

	node := lfir.NewLFIRNode(nodeType,
		fmt.Sprintf("%s_%s", item.Type, item.Key),
		"agile")

	node.Attributes["key"] = item.Key
	node.Attributes["title"] = item.Title
	node.Attributes["status"] = item.Status
	node.Attributes["priority"] = item.Priority
	node.Attributes["created_at"] = item.CreatedAt.Unix()
	node.Attributes["updated_at"] = item.UpdatedAt.Unix()
	if !item.ResolvedAt.IsZero() {
		node.Attributes["resolved_at"] = item.ResolvedAt.Unix()
		node.Attributes["cycle_time_days"] = item.ResolvedAt.Sub(item.CreatedAt).Hours() / 24
	}
	if item.TimeEstimate > 0 {
		node.Attributes["estimate_hours"] = item.TimeEstimate
	}
	if item.TimeSpent > 0 {
		node.Attributes["spent_hours"] = item.TimeSpent
	}
	if item.Blocked {
		node.Attributes["blocked"] = true
		node.Attributes["blocker_reason"] = item.BlockerReason
	}
	if len(item.Labels) > 0 {
		node.Attributes["labels"] = item.Labels
	}

	return node
}

func (b *AgileLFIRBuilder) createSprintNode(sprint Sprint) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeSprint,
		fmt.Sprintf("sprint_%s", sprint.Name), "agile")

	node.Attributes["name"] = sprint.Name
	node.Attributes["goal"] = sprint.Goal
	node.Attributes["start_date"] = sprint.StartDate.Unix()
	node.Attributes["end_date"] = sprint.EndDate.Unix()
	node.Attributes["planned_items"] = len(sprint.PlannedItemIDs)
	node.Attributes["completed_items"] = sprint.CompletedCount
	node.Attributes["velocity"] = sprint.Velocity
	node.Attributes["carry_over"] = sprint.CarryOverCount

	// Calcular coerência do sprint
	if sprint.PlannedCount > 0 {
		commitmentAccuracy := float64(sprint.CompletedCount) / float64(sprint.PlannedCount)
		scopeCreep := float64(sprint.AddedCount) / float64(sprint.PlannedCount)
		node.Attributes["commitment_accuracy"] = commitmentAccuracy
		node.Attributes["scope_creep_ratio"] = scopeCreep
	}

	return node
}

func (b *AgileLFIRBuilder) createBoardNode(boardName string) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeBoard,
		fmt.Sprintf("board_%s", boardName), "agile")
	node.Attributes["name"] = boardName
	return node
}

func (b *AgileLFIRBuilder) createColumnNode(column Column) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeColumn,
		fmt.Sprintf("column_%s", column.Name), "agile")

	node.Attributes["name"] = column.Name
	node.Attributes["wip_limit"] = column.WIPLimit
	node.Attributes["current_count"] = column.CurrentCount
	node.Attributes["avg_cycle_time_days"] = column.AvgCycleTimeDays

	if column.WIPLimit > 0 && column.CurrentCount > column.WIPLimit {
		node.Attributes["wip_exceeded"] = true
		node.Attributes["wip_excess"] = column.CurrentCount - column.WIPLimit
	}

	return node
}

func (b *AgileLFIRBuilder) findItem(items []WorkItem, id string) (WorkItem, bool) {
	for i := range items {
		if items[i].ID == id || items[i].Key == id {
			return items[i], true
		}
	}
	return WorkItem{}, false
}
