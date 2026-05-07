package models

import (
	"fmt"
	"arkhe/parser/lfir"
)

// MapToLFIR translates the API infrastructure model into the canonical LFIR graph
func MapToLFIR(api *APIInfrastructure, computeCoherence bool) (*lfir.Node, error) {
	// Create root node
	root := &lfir.Node{
		Type:       lfir.NodeTypeModule,
		Name:       fmt.Sprintf("API_%s", api.Name),
		SourceLang: api.SourceType,
		Properties: map[string]interface{}{
			"version": api.Version,
		},
		Children: make([]*lfir.Node, 0),
	}

	// Create endpoints as Operation nodes
	for _, ep := range api.Endpoints {
		epNode := &lfir.Node{
			Type:       lfir.NodeTypeOperation,
			Name:       ep.OperationID,
			SourceLang: api.SourceType,
			Properties: map[string]interface{}{
				"path":          ep.Path,
				"method":        ep.Method,
				"requires_auth": ep.RequiresAuth,
			},
		}

		if computeCoherence {
			// Stub coherence calculation
			epNode.Coherence = 0.95
		}

		root.Children = append(root.Children, epNode)
	}

	return root, nil
}
