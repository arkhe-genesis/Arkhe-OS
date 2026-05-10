package coherenceoracle

import (
	"std"
	"gno.land/p/demo/ufmt"
)

type CoherenceMetric struct {
	Timestamp int64
	Omega     float64
	Status    string
}

var history []CoherenceMetric
var individualProfiles map[string]float64

func init() {
	individualProfiles = make(map[string]float64)
}

func RecordCoherence(omega float64, status string) string {
	metric := CoherenceMetric{
		Timestamp: std.GetTimestamp().Unix(),
		Omega:     omega,
		Status:    status,
	}
	history = append(history, metric)
	return ufmt.Sprintf("Recorded Coherence: %f with status %s", omega, status)
}

func RecordIndividualBaseline(participantHash string, baseline float64) string {
	individualProfiles[participantHash] = baseline
	return ufmt.Sprintf("Recorded Baseline for %s: %f", participantHash, baseline)
}

func GetBaseline(participantHash string) float64 {
	return individualProfiles[participantHash]
}

func GetLatestCoherence() string {
	if len(history) == 0 {
		return "No metrics recorded yet"
	}
	latest := history[len(history)-1]
	return ufmt.Sprintf("Latest Omega: %f at %d", latest.Omega, latest.Timestamp)
}

func Render(path string) string {
	res := "## Oracle of Coherence - Ω-TDA history\n"
	for _, m := range history {
		res += ufmt.Sprintf("- %d: Ω=%f (%s)\n", m.Timestamp, m.Omega, m.Status)
	}
	return res
}
