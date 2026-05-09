package integration

import (
	"testing"
)

func TestGitCoherenceMapper(t *testing.T) {
	mapper := NewGitCoherenceMapper(CoherenceMappingConfig{}, nil)
	if mapper == nil {
		t.Fatalf("Expected non-nil mapper")
	}
}

func TestGitHubCoherenceMapper(t *testing.T) {
	mapper := NewGitHubCoherenceMapper(GitHubCoherenceConfig{}, nil)
	if mapper == nil {
		t.Fatalf("Expected non-nil mapper")
	}
}
