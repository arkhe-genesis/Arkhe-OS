package analyzers

import "arkhe/parser/frontends/agile/models"

type RetroSentiment struct {
	Score float64 `json:"score"`
}

func AnalyzeRetroSentiment(retros []models.Retrospective) RetroSentiment {
	if len(retros) == 0 {
		return RetroSentiment{Score: 0.0}
	}

	// Simple heuristic: happy = +1, neutral = 0, sad = -1
	totalScore := 0.0
	totalVotes := 0

	for _, retro := range retros {
		for sentiment, count := range retro.SentimentVotes {
			switch sentiment {
			case "happy":
				totalScore += float64(count)
				totalVotes += count
			case "sad":
				totalScore -= float64(count)
				totalVotes += count
			case "neutral":
				totalVotes += count
			}
		}
	}

	if totalVotes == 0 {
		return RetroSentiment{Score: 0.0}
	}

	return RetroSentiment{Score: totalScore / float64(totalVotes)}
}
