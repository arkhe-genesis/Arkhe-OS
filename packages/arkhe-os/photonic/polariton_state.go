package photonic

import (
	"time"
)

// PolaritonModeType define o tipo de modo polaritônico
type PolaritonModeType string

const (
	ModePhononPolariton  PolaritonModeType = "phonon-polariton"
	ModePlasmonPolariton PolaritonModeType = "plasmon-polariton"
	ModeExcitonPolariton PolaritonModeType = "exciton-polariton"
	ModeHybridPolariton  PolaritonModeType = "hybrid-polariton"
)

// CrystalParameters contém os parâmetros do cristal fotônico
type CrystalParameters struct {
	Material    string
	ThicknessNm float64
	Temperature float64
}

// CompressedAPIState representa o estado da API comprimido
type CompressedAPIState struct {
	StateID           string
	CompressedState   []complex128
	CompressionFactor float64
	Fidelity          float64
	PhotonicCoherence float64
	Timestamp         time.Time
	CrystalParams     CrystalParameters
}
