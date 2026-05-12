package parser

type Instruction struct {
	Opcode     string
	Arguments  []string
	Parameters map[string]string
}

type Program struct {
	Instructions []Instruction
}
