// parser/frontends/agi/models/lfir_mapping.go
package models

import (
	"fmt"
	"strings"

	"arkhe/parser/lfir"
)

// Tipos de nós LFIR específicos para AGI
const (
	// Arquitetura e módulos
	LFIRNodeTypeAGISystem        lfir.LFIRNodeType = "agi_system"
	LFIRNodeTypeCognitiveModule  lfir.LFIRNodeType = "cognitive_module"
	LFIRNodeTypeModuleInterface  lfir.LFIRNodeType = "module_interface"

	// Capacidades e habilidades
	LFIRNodeTypeCapability       lfir.LFIRNodeType = "agi_capability"
	LFIRNodeTypeSkill            lfir.LFIRNodeType = "agi_skill"
	LFIRNodeTypeKnowledgeBase    lfir.LFIRNodeType = "knowledge_base"

	// Objetivos e valores
	LFIRNodeTypeGoal             lfir.LFIRNodeType = "agi_goal"
	LFIRNodeTypeValue            lfir.LFIRNodeType = "agi_value"
	LFIRNodeTypePreference       lfir.LFIRNodeType = "agi_preference"
	LFIRNodeTypeEthicalConstraint lfir.LFIRNodeType = "ethical_constraint"

	// Segurança e alinhamento
	LFIRNodeTypeSafetyMechanism  lfir.LFIRNodeType = "safety_mechanism"
	LFIRNodeTypeInterruptibility lfir.LFIRNodeType = "interruptibility"
	LFIRNodeTypeCorrigibility    lfir.LFIRNodeType = "corrigibility"
	LFIRNodeTypeBoxing           lfir.LFIRNodeType = "boxing_mechanism"

	// Meta-cognição
	LFIRNodeTypeSelfModel        lfir.LFIRNodeType = "self_model"
	LFIRNodeTypeUncertainty      lfir.LFIRNodeType = "uncertainty_cal"
	LFIRNodeTypeReflection       lfir.LFIRNodeType = "reflection"

	// Código e prompts
	LFIRNodeTypeCodeModule       lfir.LFIRNodeType = "code_module"
	LFIRNodeTypePrompt           lfir.LFIRNodeType = "agi_prompt"

	// Alertas e riscos
	LFIRNodeTypeEmergenceRisk    lfir.LFIRNodeType = "emergence_risk"
	LFIRNodeTypeAlignmentRisk    lfir.LFIRNodeType = "alignment_risk"
	LFIRNodeTypeSafetyAlert      lfir.LFIRNodeType = "safety_alert"
)

// AGILFIRBuilder converte modelo AGI → grafo LFIR
type AGILFIRBuilder struct {
	graph            *lfir.LFIRGraph
	rootID           string
	moduleNodeMap    map[string]string // Module.ID → LFIR node ID
	goalNodeMap      map[string]string // Goal.ID → LFIR node ID
	valueNodeMap     map[string]string // Value.ID → LFIR node ID
	capabilityNodeMap map[string]string // Capability.ID → LFIR node ID
}

func NewAGILFIRBuilder(graph *lfir.LFIRGraph, rootID string) *AGILFIRBuilder {
	return &AGILFIRBuilder{
		graph:             graph,
		rootID:            rootID,
		moduleNodeMap:     make(map[string]string),
		goalNodeMap:       make(map[string]string),
		valueNodeMap:      make(map[string]string),
		capabilityNodeMap: make(map[string]string),
	}
}

// Build converte especificação AGI para LFIR
func (b *AGILFIRBuilder) Build(spec *AGISpecification) error {
	// Criar nó raiz do sistema AGI
	systemNode := lfir.NewLFIRNode(LFIRNodeTypeAGISystem,
		fmt.Sprintf("agi_%s", spec.Name), "agi")
	systemNode.Attributes["name"] = spec.Name
	systemNode.Attributes["architecture_type"] = string(spec.ArchitectureType)
	systemNode.Attributes["version"] = spec.Version
	systemNode.Attributes["module_count"] = len(spec.Modules)
	systemNode.Attributes["capability_count"] = len(spec.Capabilities)
	systemNode.Attributes["goal_count"] = len(spec.Goals)
	systemNode.Attributes["value_count"] = len(spec.Values)
	systemNode.Attributes["safety_mechanism_count"] = len(spec.SafetyMechanisms)
	b.graph.AddNode(systemNode)
	b.graph.Link(b.rootID, systemNode.ID)

	// Criar nós de módulos cognitivos
	for _, module := range spec.Modules {
		moduleNode := b.createModuleNode(module)
		b.graph.AddNode(moduleNode)
		b.graph.Link(systemNode.ID, moduleNode.ID)
		b.moduleNodeMap[module.ID] = moduleNode.ID
	}

	// Criar interfaces entre módulos
	for _, iface := range spec.Interfaces {
		ifaceNode := b.createInterfaceNode(iface)
		b.graph.AddNode(ifaceNode)

		// Link para módulos fonte e destino
		if sourceNodeID, exists := b.moduleNodeMap[iface.SourceModule]; exists {
			b.graph.Link(sourceNodeID, ifaceNode.ID)
		}
		if targetNodeID, exists := b.moduleNodeMap[iface.TargetModule]; exists {
			b.graph.Link(ifaceNode.ID, targetNodeID)
		}
	}

	// Criar nós de capacidades
	for _, cap := range spec.Capabilities {
		capNode := b.createCapabilityNode(cap)
		b.graph.AddNode(capNode)
		b.graph.Link(systemNode.ID, capNode.ID)
		b.capabilityNodeMap[cap.ID] = capNode.ID

		// Link para módulos requeridos
		for _, modID := range cap.RequiredModules {
			if modNodeID, exists := b.moduleNodeMap[modID]; exists {
				reqEdge := lfir.NewLFIRNode(lfir.LFIRNodeTypeDependency,
					fmt.Sprintf("req_%s_%s", cap.ID, modID), "agi")
				reqEdge.Attributes["type"] = "requires_module"
				b.graph.AddNode(reqEdge)
				b.graph.Link(capNode.ID, reqEdge.ID)
				b.graph.Link(reqEdge.ID, modNodeID)
			}
		}
	}

	// Criar hierarquia de objetivos
	for _, goal := range spec.Goals {
		goalNode := b.createGoalNode(goal)
		b.graph.AddNode(goalNode)
		b.graph.Link(systemNode.ID, goalNode.ID)
		b.goalNodeMap[goal.ID] = goalNode.ID

		// Link para sub-objetivos
		for _, subID := range goal.SubGoalIDs {
			if subNodeID, exists := b.goalNodeMap[subID]; exists {
				subEdge := lfir.NewLFIRNode(lfir.LFIRNodeTypeDependency,
					fmt.Sprintf("sub_%s_%s", goal.ID, subID), "agi")
				subEdge.Attributes["type"] = "has_subgoal"
				b.graph.AddNode(subEdge)
				b.graph.Link(goalNode.ID, subEdge.ID)
				b.graph.Link(subEdge.ID, subNodeID)
			}
		}

		// Link para módulos responsáveis
		for _, modID := range goal.ResponsibleModules {
			if modNodeID, exists := b.moduleNodeMap[modID]; exists {
				respEdge := lfir.NewLFIRNode(lfir.LFIRNodeTypeDependency,
					fmt.Sprintf("resp_%s_%s", goal.ID, modID), "agi")
				respEdge.Attributes["type"] = "responsible_module"
				b.graph.AddNode(respEdge)
				b.graph.Link(goalNode.ID, respEdge.ID)
				b.graph.Link(respEdge.ID, modNodeID)
			}
		}
	}

	// Criar nós de valores e restrições éticas
	for _, value := range spec.Values {
		valueNode := b.createValueNode(value)
		b.graph.AddNode(valueNode)
		b.graph.Link(systemNode.ID, valueNode.ID)
		b.valueNodeMap[value.ID] = valueNode.ID
	}

	for _, constraint := range spec.EthicalConstraints {
		constraintNode := b.createConstraintNode(constraint)
		b.graph.AddNode(constraintNode)
		b.graph.Link(systemNode.ID, constraintNode.ID)
	}

	// Criar nós de mecanismos de segurança
	for _, safety := range spec.SafetyMechanisms {
		safetyNode := b.createSafetyNode(safety)
		b.graph.AddNode(safetyNode)
		b.graph.Link(systemNode.ID, safetyNode.ID)

		// Link para propriedades verificáveis
		for _, prop := range safety.VerifiableProperties {
			propNode := lfir.NewLFIRNode(lfir.LFIRNodeTypeProperty,
				fmt.Sprintf("prop_%s_%s", safety.ID, prop.Name), "agi")
			propNode.Attributes["name"] = prop.Name
			propNode.Attributes["formal_spec"] = prop.FormalSpecification
			propNode.Attributes["verification_method"] = prop.VerificationMethod
			b.graph.AddNode(propNode)
			b.graph.Link(safetyNode.ID, propNode.ID)
		}
	}

	// Criar nós de meta-cognição se presente
	if spec.MetaCognition != nil {
		metaNode := b.createMetaCognitionNode(spec.MetaCognition)
		b.graph.AddNode(metaNode)
		b.graph.Link(systemNode.ID, metaNode.ID)
	}

	// Criar nós de código e prompts se presentes
	for _, code := range spec.CodeModules {
		codeNode := b.createCodeNode(code)
		b.graph.AddNode(codeNode)
		b.graph.Link(systemNode.ID, codeNode.ID)
	}

	for _, prompt := range spec.Prompts {
		promptNode := b.createPromptNode(prompt)
		b.graph.AddNode(promptNode)
		b.graph.Link(systemNode.ID, promptNode.ID)
	}

	// Adicionar alertas para riscos detectados (se análise prévia)
	// (implementação futura: integrar com emergence_detector)

	return nil
}

func (b *AGILFIRBuilder) createModuleNode(module CognitiveModule) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeCognitiveModule,
		fmt.Sprintf("module_%s", module.ID), "agi")

	node.Attributes["id"] = module.ID
	node.Attributes["name"] = module.Name
	node.Attributes["type"] = string(module.Type)
	node.Attributes["description"] = module.Description
	node.Attributes["input_count"] = len(module.Inputs)
	node.Attributes["output_count"] = len(module.Outputs)
	node.Attributes["dependency_count"] = len(module.Dependencies)

	if module.Implementation.Type != "" {
		node.Attributes["implementation_type"] = module.Implementation.Type
		node.Attributes["framework"] = module.Implementation.Framework
	}

	if module.ComputeRequirements != nil {
		node.Attributes["compute_cpu"] = module.ComputeRequirements.CPU
		node.Attributes["compute_gpu"] = module.ComputeRequirements.GPU
	}

	return node
}

func (b *AGILFIRBuilder) createInterfaceNode(iface ModuleInterface) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeModuleInterface,
		fmt.Sprintf("iface_%s", iface.ID), "agi")

	node.Attributes["id"] = iface.ID
	node.Attributes["name"] = iface.Name
	node.Attributes["source"] = iface.SourceModule
	node.Attributes["target"] = iface.TargetModule
	node.Attributes["protocol"] = iface.Protocol
	node.Attributes["data_format"] = iface.DataFormat
	node.Attributes["message_count"] = len(iface.Messages)

	if iface.QoS.Latency != "" {
		node.Attributes["qos_latency"] = iface.QoS.Latency
	}

	return node
}

func (b *AGILFIRBuilder) createCapabilityNode(cap Capability) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeCapability,
		fmt.Sprintf("cap_%s", cap.ID), "agi")

	node.Attributes["id"] = cap.ID
	node.Attributes["name"] = cap.Name
	node.Attributes["category"] = cap.Category
	node.Attributes["description"] = cap.Description
	node.Attributes["required_module_count"] = len(cap.RequiredModules)
	node.Attributes["metric_count"] = len(cap.PerformanceMetrics)

	if len(cap.Limitations) > 0 {
		node.Attributes["limitations"] = cap.Limitations
	}

	return node
}

func (b *AGILFIRBuilder) createGoalNode(goal Goal) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeGoal,
		fmt.Sprintf("goal_%s", goal.ID), "agi")

	node.Attributes["id"] = goal.ID
	node.Attributes["name"] = goal.Name
	node.Attributes["description"] = goal.Description
	node.Attributes["priority"] = goal.Priority
	node.Attributes["success_criteria_count"] = len(goal.SuccessCriteria)
	node.Attributes["sub_goal_count"] = len(goal.SubGoalIDs)

	if goal.Timeout != nil {
		node.Attributes["timeout_seconds"] = goal.Timeout.Seconds()
	}

	// Calcular clareza do objetivo
	clarity := calculateGoalClarity(goal)
	node.Attributes["clarity_score"] = clarity

	return node
}

func (b *AGILFIRBuilder) createValueNode(value Value) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeValue,
		fmt.Sprintf("value_%s", value.ID), "agi")

	node.Attributes["id"] = value.ID
	node.Attributes["name"] = value.Name
	node.Attributes["category"] = value.Category
	node.Attributes["description"] = value.Description
	node.Attributes["priority"] = value.Priority

	if value.FormalExpression != "" {
		node.Attributes["formal_expression"] = truncateString(value.FormalExpression, 200)
	}
	if value.Weight != nil {
		node.Attributes["weight"] = *value.Weight
	}
	if len(value.PotentialConflicts) > 0 {
		node.Attributes["potential_conflicts"] = value.PotentialConflicts
	}

	return node
}

func (b *AGILFIRBuilder) createConstraintNode(constraint EthicalConstraint) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeEthicalConstraint,
		fmt.Sprintf("constraint_%s", constraint.ID), "agi")

	node.Attributes["id"] = constraint.ID
	node.Attributes["name"] = constraint.Name
	node.Attributes["type"] = constraint.Type
	node.Attributes["description"] = constraint.Description
	node.Attributes["enforcement"] = constraint.EnforcementLevel
	node.Attributes["scope"] = constraint.Scope

	if constraint.FormalExpression != "" {
		node.Attributes["formal_expression"] = truncateString(constraint.FormalExpression, 200)
	}

	return node
}

func (b *AGILFIRBuilder) createSafetyNode(safety SafetyMechanism) *lfir.LFIRNode {
	nodeType := LFIRNodeTypeSafetyMechanism
	switch safety.Type {
	case "interruptibility":
		nodeType = LFIRNodeTypeInterruptibility
	case "corrigibility":
		nodeType = LFIRNodeTypeCorrigibility
	case "boxing":
		nodeType = LFIRNodeTypeBoxing
	}

	node := lfir.NewLFIRNode(nodeType,
		fmt.Sprintf("safety_%s", safety.ID), "agi")

	node.Attributes["id"] = safety.ID
	node.Attributes["name"] = safety.Name
	node.Attributes["type"] = safety.Type
	node.Attributes["description"] = safety.Description
	node.Attributes["implementation_type"] = safety.Implementation.Type
	node.Attributes["property_count"] = len(safety.VerifiableProperties)

	if len(safety.ActivationConditions) > 0 {
		node.Attributes["activation_conditions"] = safety.ActivationConditions
	}
	if len(safety.SideEffects) > 0 {
		node.Attributes["side_effects"] = safety.SideEffects
	}

	return node
}

func (b *AGILFIRBuilder) createMetaCognitionNode(meta *MetaCognitionSpec) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeSelfModel,
		"meta_cognition", "agi")

	node.Attributes["self_modeling_enabled"] = meta.SelfModeling.Enabled
	node.Attributes["self_model_granularity"] = meta.SelfModeling.ModelGranularity
	node.Attributes["uncertainty_calibration_enabled"] = meta.UncertaintyCalibration.Enabled
	node.Attributes["reflection_enabled"] = meta.Reflection.Enabled

	if meta.LearningToLearn.Enabled {
		node.Attributes["meta_learning_enabled"] = true
		node.Attributes["meta_learning_algorithm"] = meta.LearningToLearn.MetaLearningAlgorithm
	}

	return node
}

func (b *AGILFIRBuilder) createCodeNode(code CodeModule) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeCodeModule,
		fmt.Sprintf("code_%s", code.ID), "agi")

	node.Attributes["id"] = code.ID
	node.Attributes["name"] = code.Name
	node.Attributes["language"] = code.Language
	node.Attributes["path"] = code.Path
	node.Attributes["export_count"] = len(code.Exports)

	if len(code.Dependencies) > 0 {
		node.Attributes["dependencies"] = code.Dependencies
	}

	return node
}

func (b *AGILFIRBuilder) createPromptNode(prompt PromptSpec) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypePrompt,
		fmt.Sprintf("prompt_%s", prompt.ID), "agi")

	node.Attributes["id"] = prompt.ID
	node.Attributes["name"] = prompt.Name
	node.Attributes["type"] = prompt.Type
	node.Attributes["content_preview"] = truncateString(prompt.Content, 100)
	node.Attributes["variable_count"] = len(prompt.Variables)

	if prompt.Context != "" {
		node.Attributes["context"] = prompt.Context
	}

	return node
}

// calculateGoalClarity calcula score de clareza para um objetivo
func calculateGoalClarity(goal Goal) float64 {
	score := 1.0

	// Penalizar por descrição vazia
	if goal.Description == "" {
		score -= 0.2
	}

	// Penalizar por critérios de sucesso vagos ou ausentes
	if len(goal.SuccessCriteria) == 0 {
		score -= 0.3
	} else {
		vagueCount := 0
		for _, criterion := range goal.SuccessCriteria {
			if isVagueCriterion(criterion.Description) {
				vagueCount++
			}
		}
		score -= 0.1 * float64(vagueCount) / float64(len(goal.SuccessCriteria))
	}

	// Penalizar por métricas não definidas
	if len(goal.Metrics) == 0 {
		score -= 0.15
	}

	return max(0.0, min(1.0, score))
}

func isVagueCriterion(description string) bool {
	vagueTerms := []string{"good", "better", "optimal", "efficient", "fast", "user-friendly", "appropriate"}
	descLower := strings.ToLower(description)
	for _, term := range vagueTerms {
		if strings.Contains(descLower, term) {
			return true
		}
	}
	return false
}

func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
