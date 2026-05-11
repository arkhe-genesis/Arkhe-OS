package git

import (
	"arkhe-direnv/internal/env"
	"crypto/sha256"
	"fmt"
	"os/exec"
	"strings"
)

func ApplyGitPhase(state *env.PhaseState) error {
	cmd := exec.Command("git", "rev-parse", "HEAD")
	out, err := cmd.Output()
	if err != nil {
		// Not a git repo, skip
		return nil
	}

	hash := strings.TrimSpace(string(out))
	state.EnvVars["ARKHE_GIT_COMMIT"] = hash

	// Convert Hash to Phase Signature (as described in Deliberation #363-Ω)
	phaseSignature := generatePhaseSignature(hash)
	state.EnvVars["ARKHE_PHASE_SIGNATURE"] = phaseSignature
	state.EnvVars["ARKHE_TEMPORAL_FLOW"] = "LINEAR"
	state.EnvVars["ARKHE_CAUSALITY_ENFORCE"] = "STRICT"

	return nil
}

func generatePhaseSignature(hash string) string {
	h := sha256.New()
	h.Write([]byte(hash))
	return fmt.Sprintf("0x%x", h.Sum(nil))[:18]
}
