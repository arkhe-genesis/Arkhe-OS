package frontends

import (
	"arkhe/parser/lfir"
	"math"
)

type RedoxFrontend struct{}

func (f *RedoxFrontend) ParseRedoxNode(name string, e0 float64, ratio float64, n int, compartment string) *lfir.LFIRNode {
	node := &lfir.LFIRNode{
		ID:         "redox_" + name,
		Type:       lfir.NodeType("RedoxState"),
		Attributes: make(map[string]interface{}),
	}

	potential := 0.0
	if ratio > 0 {
		potential = e0 - nernstFactor(n)*math.Log10(ratio)
	}

	node.Attributes["potential"] = potential
	node.Attributes["ratio"] = ratio
	node.Attributes["compartment"] = compartment
	node.Attributes["provenance"] = "experimental_data"

	return node
}

func (f *RedoxFrontend) AuditCoherence(nodes []*lfir.LFIRNode) float64 {
	// Simple mock for Φ_C redox audit leveraging physiologicalCovariance
	coherence := 1.0

	for _, node := range nodes {
		attrType, ok := node.Attributes["type"].(string)
		if ok && attrType == "ros_marker" {
			tox, _ := node.Attributes["toxicity_index"].(float64)
			if tox > 0 {
				coherence -= tox * 0.1
			}
		} else {
			// Basic checks based on physiological ranges
			ratio, ok := node.Attributes["ratio"].(float64)
			comp, _ := node.Attributes["compartment"].(string)
			if ok {
				if comp == "mitochondria" && node.ID == "redox_NAD+/NADH" {
					if ratio >= 7 && ratio <= 10 {
						coherence += 0.15
					} else {
						coherence -= 0.1
					}
				}
			}
		}
	}

	if coherence > 1.0 {
		coherence = 1.0
	}
	if coherence < 0.0 {
		coherence = 0.0
	}

	return coherence
}
