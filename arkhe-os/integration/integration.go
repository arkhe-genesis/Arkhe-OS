package integration

import "time"

type ParserConfig struct {
	EnableNvidiaSMI bool
	EnableLogParsing bool
}

type Node struct {
	Type string
	Attributes map[string]string
}

type Graph struct {
	Nodes []Node
}

type DataCenterFrontend struct {
}

func NewDataCenterFrontend(clusterID string, config ParserConfig) (*DataCenterFrontend, error) {
	return &DataCenterFrontend{}, nil
}

func (d *DataCenterFrontend) Parse(output []byte) (*Graph, error) {
	return &Graph{}, nil
}

type Potential struct {
	Fired bool
}

type GradientToActionPotentialMapper struct {
}

func (g *GradientToActionPotentialMapper) MapGradientToPotential(id string, grad []float64, t time.Time) Potential {
	return Potential{}
}

type EMCoherenceMonitor struct {
}
