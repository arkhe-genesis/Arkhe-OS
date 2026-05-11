package evolution

import (
	"fmt"
	"math"
	"sync"
)

// ─── CONSTANTES DE OTIMIZAÇÃO φ ─────────────────────────────────────

const (
	// PhiOptimizationDepth profundidade máxima de transformações φ
	PhiOptimizationDepth = 5

	// PhiBalanceThreshold tolerância para considerar estrutura "balanceada por φ"
	PhiBalanceThreshold = 0.05

	// MaxInlineDepth profundidade máxima para inlining de subgrafos
	MaxInlineDepth = 3

	// MemoizationPhiWindow janela φ-ótima para estratégia de memoização
	MemoizationPhiWindow = 0.618 // 1/φ
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────────────────

// PhiOptimizationRule representa uma regra de transformação φ-guiada
type PhiOptimizationRule struct {
	ID               string
	Name             string
	Description      string
	Precondition     func(*LFIRGraph, *LFIRNode) bool
	Transform        func(*LFIRGraph, *LFIRNode) (*LFIRNode, error)
	PhiImpact        float64 // Impacto esperado na coerência φ [-1, 1]
	ComplexityChange float64 // Mudança esperada na complexidade [-1, 1]
}

// PhiOptimizationEngine aplica otimizações baseadas na razão áurea
type PhiOptimizationEngine struct {
	rules   []*PhiOptimizationRule
	mu      sync.RWMutex
	metrics OptimizationMetrics
	config  OptimizationConfig
}

// OptimizationConfig contém configuração do motor de otimização
type OptimizationConfig struct {
	MaxIterations         int     // Número máximo de iterações de otimização
	MinFitnessImprovement float64 // Melhoria mínima de fitness para aceitar transformação
	EnablePhiRebalance    bool    // Habilitar rebalanceamento estrutural por φ
	EnableMemoization     bool    // Habilitar adição estratégica de memoização
	EnableInlining        bool    // Habilitar inlining de subgrafos φ-ótimos
	Seed                  int64   // Seed para reprodutibilidade
}

// OptimizationMetrics contém métricas do processo de otimização
type OptimizationMetrics struct {
	RulesApplied          int64   `json:"rules_applied"`
	PhiCoherenceGain      float64 `json:"phi_coherence_gain"`
	ComplexityReduction   float64 `json:"complexity_reduction"`
	AvgFitnessImprovement float64 `json:"avg_fitness_improvement"`
	OptimizationsRejected int64   `json:"optimizations_rejected"`
}

// ─── CONSTRUTORES ───────────────────────────────────────────────────

// NewPhiOptimizationEngine cria novo motor de otimização φ
func NewPhiOptimizationEngine(config OptimizationConfig) *PhiOptimizationEngine {
	engine := &PhiOptimizationEngine{
		config: config,
		rules:  buildDefaultPhiRules(),
	}
	return engine
}

// buildDefaultPhiRules constrói conjunto padrão de regras de otimização φ
func buildDefaultPhiRules() []*PhiOptimizationRule {
	return []*PhiOptimizationRule{
		{
			ID:          "phi_rebalance_tree",
			Name:        "Φ-Rebalance Tree",
			Description: "Rebalancear árvore de decisões para razão depth/breadth ≈ φ",
			Precondition: func(g *LFIRGraph, n *LFIRNode) bool {
				return n.Type == LFIRConditional && g.SubgraphDepth(n) > 3
			},
			Transform:        phiRebalanceTree,
			PhiImpact:        0.15,
			ComplexityChange: -0.05,
		},
		{
			ID:          "phi_fuse_sequential",
			Name:        "Φ-Fuse Sequential",
			Description: "Fundir nós sequenciais quando razão de operações ≈ φ",
			Precondition: func(g *LFIRGraph, n *LFIRNode) bool {
				return n.Type == LFIROperation && len(n.Children) == 1 &&
					n.Children[0].Type == LFIROperation
			},
			Transform:        phiFuseSequential,
			PhiImpact:        0.08,
			ComplexityChange: -0.1,
		},
		{
			ID:          "phi_inline_subgraph",
			Name:        "Φ-Inline Subgraph",
			Description: "Inline de subgrafo quando tamanho ≈ φ^k do contexto",
			Precondition: func(g *LFIRGraph, n *LFIRNode) bool {
				return n.Type == LFIRFunctionCall && g.SubgraphSize(n) < 20
			},
			Transform:        phiInlineSubgraph,
			PhiImpact:        0.05,
			ComplexityChange: -0.02,
		},
		{
			ID:          "phi_unroll_recursion",
			Name:        "Φ-Unroll Recursion",
			Description: "Desenrolar recursão φ vezes para casos base φ-ótimos",
			Precondition: func(g *LFIRGraph, n *LFIRNode) bool {
				return n.Type == LFIRRecursiveCall && g.RecursionDepth(n) > 2
			},
			Transform:        phiUnrollRecursion,
			PhiImpact:        0.12,
			ComplexityChange: -0.08,
		},
		{
			ID:          "phi_memoize_hotspot",
			Name:        "Φ-Memoize Hotspot",
			Description: "Adicionar memoização em pontos quentes com padrão φ de acesso",
			Precondition: func(g *LFIRGraph, n *LFIRNode) bool {
				return n.Type == LFIRPureComputation && g.AccessFrequency(n) > 10
			},
			Transform:        phiAddMemoization,
			PhiImpact:        0.10,
			ComplexityChange: 0.03, // Leve aumento de complexidade por cache
		},
	}
}

// ─── OPERAÇÕES DE OTIMIZAÇÃO ────────────────────────────────────────

// Optimize aplica otimizações φ a um grafo LFIR
func (e *PhiOptimizationEngine) Optimize(
	graph *LFIRGraph,
	targetPhiCoherence float64,
) (*LFIRGraph, []EvolutionOp, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	currentGraph := graph.Clone()
	appliedOps := []EvolutionOp{}
	currentPhi := computePhiCoherence(currentGraph)

	for iter := 0; iter < e.config.MaxIterations; iter++ {
		// Verificar se já atingimos coerência φ alvo
		if math.Abs(currentPhi-targetPhiCoherence) < PhiBalanceThreshold {
			break
		}

		// Encontrar melhor regra aplicável
		bestRule, bestNode, _ := e.findBestRule(currentGraph, targetPhiCoherence)
		if bestRule == nil {
			break // Nenhuma regra aplicável com score positivo
		}

		// Aplicar transformação
		newNode, err := bestRule.Transform(currentGraph, bestNode)
		if err != nil {
			e.metrics.OptimizationsRejected++
			continue
		}

		// Atualizar grafo
		currentGraph.ReplaceNode(bestNode.ID, newNode)

		// Registrar operação aplicada
		op := evolutionOpFromRuleID(bestRule.ID)
		appliedOps = append(appliedOps, op)

		// Atualizar métricas
		newPhi := computePhiCoherence(currentGraph)
		e.metrics.RulesApplied++
		e.metrics.PhiCoherenceGain += newPhi - currentPhi
		currentPhi = newPhi

		// Verificar melhoria mínima de fitness (simplificado)
		if iter > 0 && (newPhi-currentPhi) < e.config.MinFitnessImprovement {
			break
		}
	}

	return currentGraph, appliedOps, nil
}

// findBestRule encontra a regra de otimização com maior score esperado
func (e *PhiOptimizationEngine) findBestRule(
	graph *LFIRGraph,
	targetPhi float64,
) (*PhiOptimizationRule, *LFIRNode, float64) {
	var bestRule *PhiOptimizationRule
	var bestNode *LFIRNode
	bestScore := -math.MaxFloat64

	for _, rule := range e.rules {
		// Filtrar regras por configuração
		if rule.ID == "phi_rebalance_tree" && !e.config.EnablePhiRebalance {
			continue
		}
		if rule.ID == "phi_memoize_hotspot" && !e.config.EnableMemoization {
			continue
		}
		if rule.ID == "phi_inline_subgraph" && !e.config.EnableInlining {
			continue
		}

		// Encontrar nós que satisfazem precondição
		for _, node := range graph.Nodes {
			if !rule.Precondition(graph, node) {
				continue
			}

			// Calcular score esperado da transformação
			score := e.computeRuleScore(rule, graph, node, targetPhi)
			if score > bestScore {
				bestScore = score
				bestRule = rule
				bestNode = node
			}
		}
	}

	return bestRule, bestNode, bestScore
}

// computeRuleScore calcula score esperado para aplicação de regra
func (e *PhiOptimizationEngine) computeRuleScore(
	rule *PhiOptimizationRule,
	graph *LFIRGraph,
	node *LFIRNode,
	targetPhi float64,
) float64 {
	currentPhi := computePhiCoherence(graph)

	// Componentes do score:
	// 1. Proximidade com φ alvo após transformação
	phiAfter := math.Min(1.0, currentPhi+rule.PhiImpact)
	phiScore := 1.0 - math.Abs(phiAfter-targetPhi)

	// 2. Redução de complexidade
	complexityScore := -rule.ComplexityChange // Negativo porque redução é boa

	// 3. Impacto na pureza (transformações não devem introduzir side-effects)
	purityScore := 1.0 // Assumir neutro; em produção: analisar efeitos

	// 4. Custo computacional da transformação (penalizar regras caras)
	costPenalty := 0.1 * ruleComplexityCost(rule)

	// Combinação ponderada
	score := 0.5*phiScore + 0.3*complexityScore + 0.15*purityScore - costPenalty
	return score
}

// ruleComplexityCost estima custo computacional de aplicar regra
func ruleComplexityCost(rule *PhiOptimizationRule) float64 {
	costs := map[string]float64{
		"phi_rebalance_tree":   0.3,
		"phi_fuse_sequential":  0.1,
		"phi_inline_subgraph":  0.2,
		"phi_unroll_recursion": 0.4,
		"phi_memoize_hotspot":  0.25,
	}
	return costs[rule.ID]
}

// evolutionOpFromRuleID mapeia ID de regra para EvolutionOp
func evolutionOpFromRuleID(ruleID string) EvolutionOp {
	mapping := map[string]EvolutionOp{
		"phi_rebalance_tree":   OpPhiRebalance,
		"phi_fuse_sequential":  OpNodeFusion,
		"phi_inline_subgraph":  OpSubgraphInline,
		"phi_unroll_recursion": OpRecursionUnroll,
		"phi_memoize_hotspot":  OpMemoizationAdd,
	}
	if op, ok := mapping[ruleID]; ok {
		return op
	}
	return EvolutionOp(fmt.Sprintf("custom_%s", ruleID))
}

// ─── TRANSFORMAÇÕES φ ESPECÍFICAS ───────────────────────────────────

// phiRebalanceTree rebalanceia árvore de decisões para razão φ
func phiRebalanceTree(graph *LFIRGraph, node *LFIRNode) (*LFIRNode, error) {
	// Implementação simplificada: reorganizar filhos para balancear por φ
	// Em produção: algoritmo completo de rebalanceamento de árvore AVL/φ

	// Calcular número ideal de filhos por nível baseado em φ
	idealChildren := int(math.Round(PhiTarget)) // ~1.618 → arredondar para 2

	// Se nó tem muitos filhos, agrupar em sub-árvores φ-ótimas
	if len(node.Children) > idealChildren*2 {
		// Criar nó intermediário para agrupar filhos
		groupSize := int(math.Ceil(float64(len(node.Children)) / PhiTarget))
		newChildren := []*LFIRNode{}

		for i := 0; i < len(node.Children); i += groupSize {
			end := i + groupSize
			if end > len(node.Children) {
				end = len(node.Children)
			}

			// Criar nó agrupador
			groupNode := &LFIRNode{
				ID:       fmt.Sprintf("phi_group_%s_%d", node.ID, i/groupSize),
				Type:     LFIRSequence,
				Children: node.Children[i:end],
			}
			newChildren = append(newChildren, groupNode)
		}

		node.Children = newChildren
	}

	return node, nil
}

// phiFuseSequential funde nós sequenciais quando benéfico por φ
func phiFuseSequential(graph *LFIRGraph, node *LFIRNode) (*LFIRNode, error) {
	// Fundir node com seu único filho se ambos são operações puras
	child := node.Children[0]

	// Verificar compatibilidade de tipos e ausência de conflitos
	if !canFuse(node, child) {
		return node, nil
	}

	// Criar nó fundido
	fused := &LFIRNode{
		ID:         fmt.Sprintf("fused_%s_%s", node.ID, child.ID),
		Type:       LFIRFusedOperation,
		Attributes: mergeAttributes(node.Attributes, child.Attributes),
		Children:   child.Children, // Manter filhos do segundo nó
	}

	// Atualizar referências no grafo
	graph.UpdateReferences(node.ID, fused.ID)

	return fused, nil
}

// canFuse verifica se dois nós podem ser fundidos seguramente
func canFuse(a, b *LFIRNode) bool {
	// Não fundir se algum tem efeitos colaterais
	if hasSideEffects(a) || hasSideEffects(b) {
		return false
	}

	// Verificar compatibilidade de tipos de saída/entrada
	return typesCompatible(a.OutputType, b.InputType)
}

// typesCompatible verifica compatibilidade de tipos (simplificado)
func typesCompatible(output, input *TypeInfo) bool {
	if output == nil || input == nil {
		return true // Assumir compatível se informação ausente
	}
	return output.Name == input.Name || input.Name == "any"
}

// mergeAttributes combina atributos de dois nós
func mergeAttributes(a, b map[string]interface{}) map[string]interface{} {
	result := make(map[string]interface{})
	for k, v := range a {
		result[k] = v
	}
	for k, v := range b {
		if _, exists := result[k]; !exists {
			result[k] = v
		}
	}
	return result
}

// phiInlineSubgraph realiza inlining de subgrafo quando φ-ótimo
func phiInlineSubgraph(graph *LFIRGraph, node *LFIRNode) (*LFIRNode, error) {
	// Obter subgrafo da função chamada
	calledFunc := graph.GetFunction(node.Attributes["target_function"].(string))
	if calledFunc == nil || calledFunc.Size() > 15 {
		return node, nil // Não inline se função grande
	}

	// Substituir chamada pelo corpo da função (com renomeação de variáveis)
	inlined := calledFunc.CloneWithRenaming(node.ID)

	// Conectar entradas/saídas
	graph.ConnectIO(node, inlined)

	return inlined, nil
}

// phiUnrollRecursion desenrola recursão φ vezes
func phiUnrollRecursion(graph *LFIRGraph, node *LFIRNode) (*LFIRNode, error) {
	// Desenrolar recursão para os primeiros ⌊φ⌋ = 1 níveis
	// Em produção: análise de caso base e transformação em loop

	// Criar versão não-recursiva para casos pequenos
	unrolled := createUnrolledVersion(node, 1) // 1 nível de unrolling

	return unrolled, nil
}

// createUnrolledVersion cria versão não-recursiva da função
func createUnrolledVersion(node *LFIRNode, levels int) *LFIRNode {
	// Implementação simplificada
	return &LFIRNode{
		ID:         fmt.Sprintf("unrolled_%s", node.ID),
		Type:       LFIRUnrolledRecursion,
		Attributes: node.Attributes,
		Children:   node.Children,
	}
}

// phiAddMemoization adiciona cache estratégico em ponto quente
func phiAddMemoization(graph *LFIRGraph, node *LFIRNode) (*LFIRNode, error) {
	// Envolver nó computacional com wrapper de memoização
	memoWrapper := &LFIRNode{
		ID:   fmt.Sprintf("memo_%s", node.ID),
		Type: LFIRMemoizationWrapper,
		Attributes: map[string]interface{}{
			"cache_strategy": "lru_phi", // Estratégia LRU com janela φ
			"max_entries":    int(math.Round(100 * MemoizationPhiWindow)),
			"ttl_seconds":    300,
		},
		Children: []*LFIRNode{node},
	}

	return memoWrapper, nil
}

// GetMetrics retorna métricas do motor de otimização
func (e *PhiOptimizationEngine) GetMetrics() OptimizationMetrics {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.metrics
}
