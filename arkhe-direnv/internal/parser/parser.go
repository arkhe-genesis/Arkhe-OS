package parser

import (
	"bufio"
	"io"
	"strings"
)

func Parse(r io.Reader) (*Program, error) {
	scanner := bufio.NewScanner(r)
	var instructions []Instruction

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, ";") {
			continue
		}

		instr := parseLine(line)
		instructions = append(instructions, instr)
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	return &Program{Instructions: instructions}, nil
}

func parseLine(line string) Instruction {
	// Handle directives like .DEFINE_QUASI
	if strings.HasPrefix(line, ".") {
		parts := strings.Fields(line)
		opcode := parts[0]
		var args []string
		if len(parts) > 1 {
			// Very simple parsing for .DEFINE_QUASI KEY = VALUE
			// Expecting .DEFINE_QUASI NAME = VALUE
			remaining := strings.TrimSpace(strings.TrimPrefix(line, opcode))
			args = []string{remaining}
		}
		return Instruction{Opcode: opcode, Arguments: args}
	}

	// Handle Opcodes: OP_NAME ARG1, ARG2, PARAM=VAL
	parts := strings.SplitN(line, " ", 2)
	opcode := parts[0]
	var args []string
	params := make(map[string]string)

	if len(parts) > 1 {
		rawArgs := strings.Split(parts[1], ",")
		for _, arg := range rawArgs {
			arg = strings.TrimSpace(arg)
			if strings.Contains(arg, "=") {
				kv := strings.SplitN(arg, "=", 2)
				params[strings.TrimSpace(kv[0])] = strings.TrimSpace(kv[1])
			} else {
				args = append(args, arg)
			}
		}
	}

	return Instruction{
		Opcode:     opcode,
		Arguments:  args,
		Parameters: params,
	}
}
