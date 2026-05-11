package env

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
)

type PhaseState struct {
	EnvVars    map[string]string
	Original   map[string]string
	Coherence  string
}

func NewPhaseState() *PhaseState {
	original := make(map[string]string)
	// Track critical variables to restore
	critical := []string{"PATH", "PYTHONPATH"}
	for _, v := range critical {
		original[v] = os.Getenv(v)
	}

	// Try to load backup from env if exists
	if backup := os.Getenv("_ARKHE_BACKUP"); backup != "" {
		_ = json.Unmarshal([]byte(backup), &original)
	}

	return &PhaseState{
		EnvVars:   make(map[string]string),
		Original:  original,
		Coherence: "IDLE",
	}
}

func (s *PhaseState) Export() string {
	var output string

	// Inject backup into environment so next run knows the original state
	backupData, _ := json.Marshal(s.Original)
	s.EnvVars["_ARKHE_BACKUP"] = string(backupData)

	keys := make([]string, 0, len(s.EnvVars))
	for k := range s.EnvVars {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	for _, k := range keys {
		output += fmt.Sprintf("export %s=%q\n", k, s.EnvVars[k])
	}

	if s.Coherence != "" {
		output += fmt.Sprintf("export ARKHE_COHERENCE=%q\n", s.Coherence)
	}

	return output
}

func (s *PhaseState) Relax() string {
	var output string
	// Restore original values
	for k, v := range s.Original {
		if v == "" {
			output += fmt.Sprintf("unset %s\n", k)
		} else {
			output += fmt.Sprintf("export %s=%q\n", k, v)
		}
	}
	output += "unset ARKHE_COHERENCE\n"
	output += "unset _ARKHE_BACKUP\n"
	// Also unset any ARKHE_ specific vars if we want to be thorough
	return output
}

func (s *PhaseState) GetOriginal(key string) string {
	if val, ok := s.Original[key]; ok {
		return val
	}
	return os.Getenv(key)
}
