package frontends

import "arkhe/parser/lfir"

type ReactiveOxygenSpecies struct {
    Name          string  // "O2•-", "H2O2", "•OH"
    Concentration float64 // μM
    HalfLife      float64 // ms
    Scavenger     string  // enzima que neutraliza
}

func computeToxicity(ros ReactiveOxygenSpecies) float64 {
	// Toxicidade baseada no tempo de meia-vida e concentração
	// •OH tem toxicidade mais alta
	if ros.Name == "•OH" {
		return ros.Concentration * 10.0
	} else if ros.Name == "O2•-" {
		return ros.Concentration * 5.0
	}
	return ros.Concentration * 1.0 // H2O2
}

func AnnotateROSNode(node *lfir.LFIRNode, ros ReactiveOxygenSpecies) {
	if node.Attributes == nil {
		node.Attributes = make(map[string]interface{})
	}
	node.Attributes["type"] = "ros_marker"
	node.Attributes["toxicity_index"] = computeToxicity(ros)
}
