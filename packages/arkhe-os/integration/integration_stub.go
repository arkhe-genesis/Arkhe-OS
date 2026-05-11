package integration

import (
	"arkhe/parser/lfir"
	"time"
)

type DataCenterFrontend struct{}

func (d *DataCenterFrontend) Parse(s []byte) (*lfir.LFIRGraph, error) {
	return nil, nil
}

type EMCoherenceMonitor struct{}

type ActionPotential struct {
	PotentialValue float64
	ActivationType string
	Fired          bool
}

type GradientToActionPotentialMapper struct{}

func (g *GradientToActionPotentialMapper) MapGradientToPotential(grad string, val []float64, t time.Time) ActionPotential {
	return ActionPotential{}
}

type ParserConfig struct {
	EnableNvidiaSMI  bool
	EnableLogParsing bool
}

func NewDataCenterFrontend(c string, c3 ParserConfig) (*DataCenterFrontend, error) {
	return &DataCenterFrontend{}, nil
}
