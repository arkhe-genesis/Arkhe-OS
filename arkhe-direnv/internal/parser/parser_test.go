package parser

import (
	"strings"
	"testing"
)

func TestParse(t *testing.T) {
	input := `
; comment
.DEFINE_QUASI FOO = BAR
PHASE_add /tmp
COHERENCE_set HIGH
SECRET_load MY_KEY
`
	prog, err := Parse(strings.NewReader(input))
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}

	if len(prog.Instructions) != 4 {
		t.Errorf("Expected 4 instructions, got %d", len(prog.Instructions))
	}

	if prog.Instructions[0].Opcode != ".DEFINE_QUASI" {
		t.Errorf("Expected .DEFINE_QUASI, got %s", prog.Instructions[0].Opcode)
	}
}
