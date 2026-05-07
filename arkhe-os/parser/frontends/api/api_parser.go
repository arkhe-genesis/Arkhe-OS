// parser/frontends/api/api_parser.go
package api

import (
	"fmt"
	"path/filepath"
	"strings"

	"arkhe/parser/frontends/api/formats"
	"arkhe/parser/frontends/api/models"
	"arkhe/parser/lfir"
)

type APIParser struct {
	Framework string
}

func NewAPIParser() *APIParser {
	return &APIParser{}
}

func (p *APIParser) Parse(source []byte, filename string, options map[string]interface{}) (*lfir.LFIRGraph, error) {
	dataType := detectAPIDataType(filename)

	var apiSpec *models.APISpecification
	var err error

	switch dataType {
	case "xml_api_spec":
		apiSpec, err = formats.ParseXMLAPISpec(source)
	default:
		return nil, fmt.Errorf("unsupported API specification format: %s", dataType)
	}

	if err != nil {
		return nil, err
	}

	return p.mapToLFIR(apiSpec)
}

func detectAPIDataType(filename string) string {
	ext := strings.ToLower(filepath.Ext(filename))
	switch ext {
	case ".xml", ".wsdl":
		return "xml_api_spec"
	default:
		return "unknown"
	}
}

func (p *APIParser) mapToLFIR(spec *models.APISpecification) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()

	rootNode := &lfir.LFIRNode{
		ID:   "root",
		Type: lfir.NodeTypeSystem,
		Attributes: map[string]interface{}{
			"system_name":             spec.Name,
			"version":                 spec.Version,
			"service_count":           len(spec.Services),
			"endpoint_count":          countEndpoints(spec),
			"coherence_auth_coverage": calculateAuthCoverage(spec),
			"coherence_resilience":    calculateResilience(spec),
		},
	}
	graph.AddNode(rootNode)
	graph.RootNodes = append(graph.RootNodes, rootNode.ID)

	// Just stub out metrics for now
	graph.Metrics.CoherenceScore = 0.9

	return graph, nil
}

func countEndpoints(spec *models.APISpecification) int {
	count := 0
	for _, srv := range spec.Services {
		count += len(srv.Endpoints)
	}
	return count
}

func calculateAuthCoverage(spec *models.APISpecification) float64 {
	if len(spec.Services) == 0 {
		return 0.0
	}

	totalEndpoints := 0
	securedEndpoints := 0

	for _, srv := range spec.Services {
		for _, ep := range srv.Endpoints {
			totalEndpoints++
			if len(ep.Security) > 0 {
				securedEndpoints++
			}
		}
	}

	if totalEndpoints == 0 {
		return 1.0 // no endpoints = fully covered
	}

	return float64(securedEndpoints) / float64(totalEndpoints)
}

func calculateResilience(spec *models.APISpecification) float64 {
	if len(spec.Services) == 0 {
		return 0.0
	}

	totalEndpoints := 0
	resilientEndpoints := 0

	for _, srv := range spec.Services {
		for _, ep := range srv.Endpoints {
			totalEndpoints++

			// Simple heuristic
			if ep.Resilience.Retry != nil || ep.Resilience.CircuitBreaker != nil || ep.Resilience.Timeout != "" {
				resilientEndpoints++
			}
		}
	}

	if totalEndpoints == 0 {
		return 1.0
	}

	return float64(resilientEndpoints) / float64(totalEndpoints)
}
