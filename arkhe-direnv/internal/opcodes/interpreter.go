package opcodes

import (
	"arkhe-direnv/internal/env"
	"arkhe-direnv/internal/parser"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type Interpreter struct {
	State *env.PhaseState
}

func NewInterpreter(state *env.PhaseState) *Interpreter {
	return &Interpreter{State: state}
}

func (i *Interpreter) Execute(prog *parser.Program) error {
	for _, instr := range prog.Instructions {
		switch instr.Opcode {
		case ".DEFINE_QUASI":
			i.handleDefineQuasi(instr)
		case "PHASE_add":
			i.handlePhaseAdd(instr)
		case "PYTHONPATH_add":
			i.handlePythonPathAdd(instr)
		case "SYS_HARMONIZE", "COHERENCE_set":
			i.handleCoherenceSet(instr)
		case "AKASHA_DECRYSTALLIZE", "SECRET_load":
			i.handleSecretLoad(instr)
		case "NEURAL_SYNC", "NEURAL_focus":
			i.handleNeuralSync(instr)
		case "VACUUM_RELAX", "VACUUM_RELAX_V2", "VACUUM_RELAX_ADIABATIC":
			i.handleVacuumRelax(instr)
		case "LAYOUT_python":
			i.handleLayoutPython(instr)
		default:
			// Generic handling for unknown opcodes
			fmt.Fprintf(os.Stderr, "arkhe-direnv: unknown opcode %s\n", instr.Opcode)
		}
	}
	return nil
}

func (i *Interpreter) handleDefineQuasi(instr parser.Instruction) {
	if len(instr.Arguments) > 0 {
		kv := strings.SplitN(instr.Arguments[0], "=", 2)
		if len(kv) == 2 {
			key := strings.TrimSpace(kv[0])
			val := strings.TrimSpace(kv[1])
			i.State.EnvVars[key] = val
		}
	}
}

func (i *Interpreter) handlePhaseAdd(instr parser.Instruction) {
	if len(instr.Arguments) > 0 {
		path := instr.Arguments[0]
		currentPath := i.State.EnvVars["PATH"]
		if currentPath == "" {
			currentPath = i.State.GetOriginal("PATH")
		}
		i.State.EnvVars["PATH"] = path + ":" + currentPath
	}
}

func (i *Interpreter) handlePythonPathAdd(instr parser.Instruction) {
	if len(instr.Arguments) > 0 {
		path := instr.Arguments[0]
		current := i.State.EnvVars["PYTHONPATH"]
		if current == "" {
			current = i.State.GetOriginal("PYTHONPATH")
		}
		if current != "" {
			i.State.EnvVars["PYTHONPATH"] = path + ":" + current
		} else {
			i.State.EnvVars["PYTHONPATH"] = path
		}
	}
}

func (i *Interpreter) handleCoherenceSet(instr parser.Instruction) {
	level := "MEDIUM"
	if len(instr.Arguments) > 0 {
		level = instr.Arguments[0]
	} else if l, ok := instr.Parameters["PRIORITY"]; ok {
		level = l
	}
	i.State.Coherence = level
	i.State.EnvVars["ARKHE_COHERENCE"] = level
}

func (i *Interpreter) handleSecretLoad(instr parser.Instruction) {
	if len(instr.Arguments) > 0 {
		key := instr.Arguments[0]
		// Simulation: In a real system, it would fetch from Akasha
		i.State.EnvVars[key] = "ark_live_simulated_secret"
	}
}

func (i *Interpreter) handleNeuralSync(instr parser.Instruction) {
	if focus, ok := instr.Parameters["FOCUS"]; ok {
		i.State.EnvVars["ARKHE_NEURAL_FOCUS"] = focus
	}
}

func (i *Interpreter) handleVacuumRelax(instr parser.Instruction) {
	i.State.Coherence = "RELAXING"
	i.State.EnvVars["ARKHE_RELAX_MODE"] = "ADIABATIC"
	if tau, ok := instr.Parameters["TAU"]; ok {
		i.State.EnvVars["ARKHE_RELAX_TAU"] = tau
	} else {
		i.State.EnvVars["ARKHE_RELAX_TAU"] = "500ms"
	}
}

func (i *Interpreter) handleLayoutPython(instr parser.Instruction) {
	// Simple venv detection and activation simulation
	if _, err := os.Stat(".venv"); err == nil {
		abs, _ := filepath.Abs(".venv/bin")
		currentPath := i.State.GetOriginal("PATH")
		i.State.EnvVars["PATH"] = abs + ":" + currentPath
		i.State.EnvVars["VIRTUAL_ENV"] = filepath.Dir(abs)
	}
}
