package frontends

import (
	"testing"
)

func TestGitHubFrontend(t *testing.T) {
	frontend, err := NewGitHubFrontend("owner", "repo", GitHubParserConfig{})
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	if frontend.GetLanguage() != "github" {
		t.Fatalf("Expected language github, got %s", frontend.GetLanguage())
	}
}

func TestGitWorkflowFrontend(t *testing.T) {
	frontend := NewGitWorkflowFrontend(".", GitParserConfig{})
	if frontend.GetLanguage() != "git" {
		t.Fatalf("Expected language git, got %s", frontend.GetLanguage())
	}
}
