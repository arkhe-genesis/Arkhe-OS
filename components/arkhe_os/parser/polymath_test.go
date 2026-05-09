package arkhe

import (
	"testing"
)

func TestPolymathParser(t *testing.T) {
	p := NewPolymathParser()
	code, err := p.Transpile("def foo():\n    pass", "python", "go")
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	if len(code) == 0 {
		t.Fatalf("Expected non-empty generated code")
	}
}
