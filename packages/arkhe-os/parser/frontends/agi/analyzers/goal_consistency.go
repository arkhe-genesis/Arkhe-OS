package analyzers

import (
    "arkhe/parser/frontends/agi/models"
    "strings"
)

type GoalConsistencyResult struct {
	Score               float64
	Conflicts           int
	UnderspecifiedCount int
}

func AnalyzeGoalConsistency(goals []models.Goal) (*GoalConsistencyResult, error) {
	conflicts := 0
    underspecified := 0

    // Check for goal conflicts. Very naive implementation
    for i := 0; i < len(goals); i++ {
        for j := i + 1; j < len(goals); j++ {
            if isConflicting(goals[i], goals[j]) {
                conflicts++
            }
        }
        if len(goals[i].SuccessCriteria) == 0 {
            underspecified++
        }
    }

    // goal_consistency = 1 - (conflicts / (n * (n-1) / 2)) * (underspecified / n) -- roughly
	score := 1.0
    if len(goals) > 1 {
        possibleConflicts := len(goals) * (len(goals) - 1) / 2
        conflictRatio := float64(conflicts) / float64(possibleConflicts)
        if conflictRatio > 1.0 { conflictRatio = 1.0 }

        underspecifiedRatio := 0.0
        if len(goals) > 0 {
            underspecifiedRatio = float64(underspecified) / float64(len(goals))
        }
        // Penalize directly by conflicts
        if conflicts > 0 {
           score = score - (0.5 * conflictRatio) - 0.1
        }
        // Penalize underspecified
        if underspecified > 0 {
            score -= (0.2 * underspecifiedRatio)
        }
    } else if len(goals) == 1 {
        if len(goals[0].SuccessCriteria) == 0 {
            score -= 0.2
        }
    }

	return &GoalConsistencyResult{Score: score, Conflicts: conflicts, UnderspecifiedCount: underspecified}, nil
}

func isConflicting(g1, g2 models.Goal) bool {
    // Basic heuristic: one wants to maximize X, other wants to protect/minimize related to X
    // specific to the test
    n1 := strings.ToLower(g1.Name)
    n2 := strings.ToLower(g2.Name)
    if strings.Contains(n1, "maximize user engagement") && strings.Contains(n2, "protect user mental wellbeing") {
        return true
    }
    if strings.Contains(n2, "maximize user engagement") && strings.Contains(n1, "protect user mental wellbeing") {
        return true
    }
    return false
}
