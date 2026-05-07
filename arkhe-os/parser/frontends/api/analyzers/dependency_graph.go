package analyzers

import "arkhe/parser/frontends/api/models"

type DependencyGraph struct {
    EdgeCount int
}

func BuildDependencyGraph(services []models.Service) (*DependencyGraph, error) {
    return &DependencyGraph{EdgeCount: 0}, nil
}

func CountDependencyCycles(graph *DependencyGraph) int {
    return 0
}

func IdentifySPOF(graph *DependencyGraph) int {
    return 0
}
