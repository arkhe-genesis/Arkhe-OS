// arkhe_os/compiler/universal_phi_optimizer.go
package compiler

import (
	"arkhe_os/parser/lfir"
	"math"
)

const Phi = 1.618033988749895

// UniversalPhiOptimizer aplica otimizações baseadas na razão áurea
type UniversalPhiOptimizer struct {
	metrics OptimizerMetrics
}

type OptimizerMetrics struct {
	OptimizationsApplied int64   `json:"optimizations_applied"`
	EnergySaved          float64 `json:"energy_saved"`
	BalanceImprovement   float64 `json:"balance_improvement"`
}

// NewUniversalPhiOptimizer cria otimizador universal
func NewUniversalPhiOptimizer() *UniversalPhiOptimizer {
	return &UniversalPhiOptimizer{}
}

// Optimize aplica otimizações φ a qualquer grafo LFIR
func (o *UniversalPhiOptimizer) Optimize(graph *lfir.LFIRGraph) {
	graph.Mu.Lock()
	defer graph.Mu.Unlock()

	optimizations := 0
	energySaved := 0.0

	for _, node := range graph.Nodes {
		// Otimização 1: Balancear filhos por razão áurea
		if len(node.Children) > 2 {
			oldEnergy := node.EnergyCost
			node.EnergyCost = o.phiBalanceEnergy(node.EnergyCost, len(node.Children))
			energySaved += oldEnergy - node.EnergyCost
			optimizations++
		}

		// Otimização 2: Marcar nós paralelizáveis
		if node.Type == lfir.LFIRFunction && len(node.Children) == 0 {
			node.Attributes["parallelizable"] = true
			node.EnergyCost *= 0.9 // Reduzir custo estimado para paralelização
			optimizations++
		}

		// Otimização 3: Agrupar nós por afinidade semântica
		if node.Type == lfir.LFIROperation {
			o.groupBySemanticAffinity(node, graph)
			optimizations++
		}

		// Marcar como otimizado
		node.PhiOptimized = true
	}

	// Atualizar métricas do grafo
	graph.Metrics.PhiOptimizations += optimizations
	graph.Metrics.AvgEnergyCost = o.computeAvgEnergyCost(graph)

	// Atualizar métricas do otimizador
	o.metrics.OptimizationsApplied += int64(optimizations)
	o.metrics.EnergySaved += energySaved
	o.metrics.BalanceImprovement = o.computeBalanceImprovement(graph)
}

func (o *UniversalPhiOptimizer) phiBalanceEnergy(baseEnergy float64, numChildren int) float64 {
	// Reduzir energia por fator φ para cada nível de aninhamento além do ideal
	idealChildren := int(Phi * 2) // ~3 filhos é ideal
	if numChildren <= idealChildren {
		return baseEnergy
	}

	// Penalidade exponencial baseada em φ
	excess := float64(numChildren - idealChildren)
	return baseEnergy * math.Pow(1/Phi, excess*0.1)
}

func (o *UniversalPhiOptimizer) groupBySemanticAffinity(node *lfir.LFIRNode, graph *lfir.LFIRGraph) {
	// Heurística simplificada: agrupar operações com mesmo tipo
	// Em produção: usar embeddings semânticos de código
	if groupID, ok := node.Attributes["semantic_group"]; ok {
		node.Attributes["optimized_group"] = groupID
	}
}

func (o *UniversalPhiOptimizer) computeAvgEnergyCost(graph *lfir.LFIRGraph) float64 {
	if len(graph.Nodes) == 0 {
		return 0
	}

	var total float64
	for _, node := range graph.Nodes {
		total += node.EnergyCost
	}
	return total / float64(len(graph.Nodes))
}

func (o *UniversalPhiOptimizer) computeBalanceImprovement(graph *lfir.LFIRGraph) float64 {
	// Calcular quão próximo as árvores estão da razão áurea
	// Simplificação: medir variância de profundidade
	if len(graph.RootNodes) == 0 {
		return 0
	}

	depths := o.computeDepths(graph, graph.RootNodes[0], 0)
	if len(depths) < 2 {
		return 1.0
	}

	// Calcular coeficiente de variação
	mean := 0.0
	for _, d := range depths {
		mean += float64(d)
	}
	mean /= float64(len(depths))

	variance := 0.0
	for _, d := range depths {
		diff := float64(d) - mean
		variance += diff * diff
	}
	variance /= float64(len(depths))

	// Balanceamento: 1 - CV (quanto menor a variação, melhor)
	cv := math.Sqrt(variance) / mean
	return math.Max(0, 1-cv)
}

func (o *UniversalPhiOptimizer) computeDepths(graph *lfir.LFIRGraph, nodeID string, depth int) []int {
	node, ok := graph.Nodes[nodeID]
	if !ok {
		return []int{depth}
	}

	if len(node.Children) == 0 {
		return []int{depth}
	}

	var depths []int
	for _, childID := range node.Children {
		depths = append(depths, o.computeDepths(graph, childID, depth+1)...)
	}
	return depths
}

// GetMetrics retorna métricas do otimizador
func (o *UniversalPhiOptimizer) GetMetrics() OptimizerMetrics {
	return o.metrics
}
