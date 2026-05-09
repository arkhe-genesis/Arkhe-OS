package evolution

import (
	"fmt"
	"math"
	"math/rand"
	"sort"
	"sync"
	"time"
)

// ─── CONSTANTES DE SELEÇÃO NATURAL ─────────────────────────────────

const (
	// TournamentSize tamanho do torneio para seleção
	TournamentSize = 5

	// ElitismCount número de melhores indivíduos preservados por geração
	ElitismCount = 2

	// MutationRateProb probabilidade base de mutação por variante
	MutationRateProb = 0.15

	// CrossoverRateProb probabilidade de crossover entre variantes
	CrossoverRateProb = 0.7

	// MinPopulationSize tamanho mínimo da população para evolução
	MinPopulationSize = 10

	// MaxGenerations número máximo de gerações de evolução
	MaxGenerations = 50

	// ConvergenceThreshold threshold para detectar convergência da população
	ConvergenceThreshold = 0.001
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────────────────

// Population representa uma população de variantes de função
type Population struct {
	Variants    []*FunctionVariant
	Generation  int
	BestFitness float64
	AvgFitness  float64
	Diversity   float64 // Medida de diversidade genética
}

// SelectionStrategy enumera estratégias de seleção
type SelectionStrategy string

const (
	StrategyTournament SelectionStrategy = "tournament"
	StrategyRoulette   SelectionStrategy = "roulette"
	StrategyRank       SelectionStrategy = "rank"
	StrategyElitism    SelectionStrategy = "elitism"
)

// NaturalSelectionEngine implementa seleção natural para evolução de funções
type NaturalSelectionEngine struct {
	population        *Population
	fitnessWeights    map[string]float64
	selectionStrategy SelectionStrategy
	mutationRate      float64
	crossoverRate     float64
	elitismCount      int

	metrics SelectionMetrics
	mu      sync.RWMutex
	rng     *rand.Rand
}

// SelectionMetrics contém métricas do processo de seleção
type SelectionMetrics struct {
	GenerationsCompleted int64     `json:"generations_completed"`
	BestFitnessHistory   []float64 `json:"best_fitness_history"`
	AvgDiversity         float64   `json:"avg_diversity"`
	ConvergenceDetected  bool      `json:"convergence_detected"`
	SelectionPressure    float64   `json:"selection_pressure"`
}

// ─── CONSTRUTORES ───────────────────────────────────────────────────

// NewNaturalSelectionEngine cria novo motor de seleção natural
func NewNaturalSelectionEngine(
	initialVariants []*FunctionVariant,
	fitnessWeights map[string]float64,
	config map[string]interface{},
) *NaturalSelectionEngine {
	// Configurações padrão
	weights := map[string]float64{
		"time":   0.4,
		"memory": 0.3,
		"energy": 0.15,
		"phi":    0.15,
	}
	for k, v := range fitnessWeights {
		weights[k] = v
	}

	engine := &NaturalSelectionEngine{
		fitnessWeights:    weights,
		selectionStrategy: StrategyTournament,
		mutationRate:      MutationRateProb,
		crossoverRate:     CrossoverRateProb,
		elitismCount:      ElitismCount,
		rng:               rand.New(rand.NewSource(time.Now().UnixNano())),
		metrics: SelectionMetrics{
			BestFitnessHistory: make([]float64, 0, MaxGenerations),
		},
	}

	// Aplicar configurações personalizadas
	if val, ok := config["strategy"]; ok {
		if s, ok := val.(SelectionStrategy); ok {
			engine.selectionStrategy = s
		}
	}
	if val, ok := config["mutation_rate"]; ok {
		if r, ok := val.(float64); ok {
			engine.mutationRate = r
		}
	}
	if val, ok := config["crossover_rate"]; ok {
		if r, ok := val.(float64); ok {
			engine.crossoverRate = r
		}
	}

	// Inicializar população
	engine.initializePopulation(initialVariants)

	return engine
}

// initializePopulation inicializa população com variantes iniciais
func (e *NaturalSelectionEngine) initializePopulation(variants []*FunctionVariant) {
	// Calcular fitness inicial para cada variante
	for _, v := range variants {
		v.Fitness = v.ComputeFitness(e.fitnessWeights)
	}

	e.population = &Population{
		Variants:    variants,
		Generation:  0,
		BestFitness: e.findBestFitness(variants),
		AvgFitness:  e.computeAvgFitness(variants),
		Diversity:   e.computeDiversity(variants),
	}
}

// ─── OPERAÇÕES DE EVOLUÇÃO ──────────────────────────────────────────

// Evolve executa uma geração completa de evolução
func (e *NaturalSelectionEngine) Evolve() (*Population, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	currentPop := e.population
	if currentPop == nil || len(currentPop.Variants) < MinPopulationSize {
		return nil, fmt.Errorf("population too small for evolution")
	}

	// 1. Selecionar pais via estratégia configurada
	parents := e.selectParents(currentPop.Variants)

	// 2. Aplicar crossover para gerar filhos
	children := e.applyCrossover(parents)

	// 3. Aplicar mutação nos filhos
	children = e.applyMutation(children)

	// 4. Avaliar fitness dos filhos (simulado; em produção: executar em Hyper-Mesh)
	for _, child := range children {
		child.Fitness = child.ComputeFitness(e.fitnessWeights)
	}

	// 5. Selecionar próxima geração (elitismo + seleção)
	nextGeneration := e.selectNextGeneration(currentPop.Variants, children)

	// 6. Atualizar população
	newPop := &Population{
		Variants:    nextGeneration,
		Generation:  currentPop.Generation + 1,
		BestFitness: e.findBestFitness(nextGeneration),
		AvgFitness:  e.computeAvgFitness(nextGeneration),
		Diversity:   e.computeDiversity(nextGeneration),
	}

	e.population = newPop

	// 7. Atualizar métricas
	e.metrics.GenerationsCompleted++
	e.metrics.BestFitnessHistory = append(e.metrics.BestFitnessHistory, newPop.BestFitness)
	e.metrics.AvgDiversity = (e.metrics.AvgDiversity*0.99 + newPop.Diversity*0.01)

	// 8. Verificar convergência
	if e.checkConvergence() {
		e.metrics.ConvergenceDetected = true
	}

	return newPop, nil
}

// selectParents seleciona pais para reprodução baseado na estratégia
func (e *NaturalSelectionEngine) selectParents(population []*FunctionVariant) []*FunctionVariant {
	switch e.selectionStrategy {
	case StrategyTournament:
		return e.tournamentSelection(population)
	case StrategyRoulette:
		return e.rouletteSelection(population)
	case StrategyRank:
		return e.rankSelection(population)
	default:
		return e.tournamentSelection(population) // Fallback
	}
}

// tournamentSelection implementa seleção por torneio
func (e *NaturalSelectionEngine) tournamentSelection(pop []*FunctionVariant) []*FunctionVariant {
	selected := make([]*FunctionVariant, 0, len(pop))

	for i := 0; i < len(pop); i++ {
		// Selecionar TournamentSize indivíduos aleatórios
		tournament := make([]*FunctionVariant, TournamentSize)
		for j := 0; j < TournamentSize; j++ {
			idx := e.rng.Intn(len(pop))
			tournament[j] = pop[idx]
		}

		// Selecionar o melhor do torneio
		best := tournament[0]
		for _, candidate := range tournament[1:] {
			if candidate.Fitness > best.Fitness {
				best = candidate
			}
		}
		selected = append(selected, best)
	}

	return selected
}

// rouletteSelection implementa seleção por roleta (proporcional ao fitness)
func (e *NaturalSelectionEngine) rouletteSelection(pop []*FunctionVariant) []*FunctionVariant {
	// Calcular fitness total
	totalFitness := 0.0
	for _, v := range pop {
		totalFitness += math.Max(0, v.Fitness) // Garantir não-negativo
	}

	if totalFitness == 0 {
		return pop // Fallback: retornar população original
	}

	selected := make([]*FunctionVariant, 0, len(pop))

	for i := 0; i < len(pop); i++ {
		// Selecionar ponto aleatório na roleta
		spin := e.rng.Float64() * totalFitness
		current := 0.0

		for _, v := range pop {
			current += math.Max(0, v.Fitness)
			if current >= spin {
				selected = append(selected, v)
				break
			}
		}
	}

	return selected
}

// rankSelection implementa seleção por ranking
func (e *NaturalSelectionEngine) rankSelection(pop []*FunctionVariant) []*FunctionVariant {
	// Ordenar por fitness
	sorted := make([]*FunctionVariant, len(pop))
	copy(sorted, pop)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].Fitness > sorted[j].Fitness
	})

	// Atribuir pesos por rank (linear)
	weights := make([]float64, len(sorted))
	for i := range sorted {
		weights[i] = float64(len(sorted) - i)
	}

	// Selecionar baseado em pesos
	selected := make([]*FunctionVariant, 0, len(pop))
	totalWeight := 0.0
	for _, w := range weights {
		totalWeight += w
	}

	for i := 0; i < len(pop); i++ {
		spin := e.rng.Float64() * totalWeight
		current := 0.0
		for j, v := range sorted {
			current += weights[j]
			if current >= spin {
				selected = append(selected, v)
				break
			}
		}
	}

	return selected
}

// applyCrossover aplica crossover entre pares de pais
func (e *NaturalSelectionEngine) applyCrossover(parents []*FunctionVariant) []*FunctionVariant {
	children := make([]*FunctionVariant, 0, len(parents))

	for i := 0; i < len(parents); i += 2 {
		if i+1 >= len(parents) {
			// Ímpar: copiar último pai sem crossover
			children = append(children, parents[i].Clone())
			continue
		}

		parentA := parents[i]
		parentB := parents[i+1]

		// Decidir se aplica crossover
		if e.rng.Float64() > e.crossoverRate {
			children = append(children, parentA.Clone(), parentB.Clone())
			continue
		}

		// Aplicar crossover estrutural nos LFIRs
		childA, childB := crossoverLFIR(parentA, parentB, e.rng)
		children = append(children, childA, childB)
	}

	return children
}

// crossoverLFIR realiza crossover estrutural entre dois grafos LFIR
func crossoverLFIR(a, b *FunctionVariant, rng *rand.Rand) (*FunctionVariant, *FunctionVariant) {
	// Em produção: crossover real em grafos LFIR com preservação de tipos
	// Aqui: simulação simplificada

	// Criar clones como base
	childA := a.Clone()
	childB := b.Clone()

	// Trocar subconjunto de operações com probabilidade
	if rng.Float64() < 0.5 && len(childA.Operations) > 0 && len(childB.Operations) > 0 {
		// Trocar última operação
		childA.Operations, childB.Operations =
			swapLastOperation(childA.Operations, childB.Operations)
	}

	// Atualizar IDs e generation
	childA.VariantID = generateVariantID()
	childB.VariantID = generateVariantID()
	childA.Generation = a.Generation + 1
	childB.Generation = b.Generation + 1

	return childA, childB
}

// swapLastOperation troca a última operação entre duas listas
func swapLastOperation(a, b []EvolutionOp) ([]EvolutionOp, []EvolutionOp) {
	if len(a) == 0 || len(b) == 0 {
		return a, b
	}

	newA := make([]EvolutionOp, len(a))
	newB := make([]EvolutionOp, len(b))
	copy(newA, a)
	copy(newB, b)

	newA[len(newA)-1], newB[len(newB)-1] = newB[len(newB)-1], newA[len(newA)-1]
	return newA, newB
}

// generateVariantID gera ID único para nova variante
func generateVariantID() string {
	return fmt.Sprintf("var_%d_%x", time.Now().UnixNano(), rand.Int63())
}

// applyMutation aplica mutação aleatória em variantes
func (e *NaturalSelectionEngine) applyMutation(variants []*FunctionVariant) []*FunctionVariant {
	mutated := make([]*FunctionVariant, len(variants))

	for i, v := range variants {
		if e.rng.Float64() < e.mutationRate {
			mutated[i] = e.mutateVariant(v)
		} else {
			mutated[i] = v.Clone()
		}
	}

	return mutated
}

// mutateVariant aplica mutação estrutural em uma variante
func (e *NaturalSelectionEngine) mutateVariant(v *FunctionVariant) *FunctionVariant {
	mutated := v.Clone()

	// Escolher tipo de mutação aleatoriamente
	mutationTypes := []EvolutionOp{
		OpPhiRebalance, OpNodeFusion, OpSubgraphInline,
		OpRecursionUnroll, OpMemoizationAdd,
	}
	randomOp := mutationTypes[e.rng.Intn(len(mutationTypes))]

	// Aplicar mutação (simplificado: adicionar à lista de operações)
	mutated.Operations = append(mutated.Operations, randomOp)

	// Perturbar levemente métricas de execução para simular variação
	mutated.ExecutionMetrics.AvgExecutionTimeMs *= (0.9 + e.rng.Float64()*0.2)
	mutated.ExecutionMetrics.AvgMemoryUsageMB *= (0.9 + e.rng.Float64()*0.2)

	return mutated
}

// selectNextGeneration seleciona indivíduos para próxima geração
func (e *NaturalSelectionEngine) selectNextGeneration(
	current, children []*FunctionVariant,
) []*FunctionVariant {
	// Combinar população atual e filhos
	candidatePool := append(current, children...)

	// Ordenar por fitness (decrescente)
	sort.Slice(candidatePool, func(i, j int) bool {
		return candidatePool[i].Fitness > candidatePool[j].Fitness
	})

	// Preservar elite
	nextGen := make([]*FunctionVariant, 0, len(current))
	for i := 0; i < e.elitismCount && i < len(candidatePool); i++ {
		nextGen = append(nextGen, candidatePool[i].Clone())
	}

	// Preencher restante via seleção por torneio
	remaining := candidatePool[e.elitismCount:]
	for len(nextGen) < len(current) && len(remaining) > 0 {
		selected := e.tournamentSelection(remaining)
		if len(selected) > 0 {
			nextGen = append(nextGen, selected[0].Clone())
		}
		// Remover selecionado para evitar duplicatas
		if len(remaining) > 0 {
			remaining = remaining[1:]
		}
	}

	// Garantir tamanho fixo da população
	if len(nextGen) > len(current) {
		nextGen = nextGen[:len(current)]
	}

	return nextGen
}

// checkConvergence verifica se população convergiu
func (e *NaturalSelectionEngine) checkConvergence() bool {
	history := e.metrics.BestFitnessHistory
	if len(history) < 10 {
		return false
	}

	// Verificar se melhoria nas últimas 10 gerações é insignificante
	recent := history[len(history)-10:]
	improvement := recent[len(recent)-1] - recent[0]

	return math.Abs(improvement) < ConvergenceThreshold
}

// Helper functions
func (e *NaturalSelectionEngine) findBestFitness(variants []*FunctionVariant) float64 {
	if len(variants) == 0 {
		return 0
	}
	best := variants[0].Fitness
	for _, v := range variants[1:] {
		if v.Fitness > best {
			best = v.Fitness
		}
	}
	return best
}

func (e *NaturalSelectionEngine) computeAvgFitness(variants []*FunctionVariant) float64 {
	if len(variants) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range variants {
		sum += v.Fitness
	}
	return sum / float64(len(variants))
}

func (e *NaturalSelectionEngine) computeDiversity(variants []*FunctionVariant) float64 {
	if len(variants) < 2 {
		return 1.0
	}

	// Diversidade como distância média entre vetores de assinatura
	sumDist := 0.0
	count := 0
	for i := 0; i < len(variants); i++ {
		for j := i + 1; j < len(variants); j++ {
			dist := euclideanDistance(variants[i].toVector(), variants[j].toVector())
			sumDist += dist
			count++
		}
	}

	if count == 0 {
		return 1.0
	}
	return sumDist / float64(count)
}

// toVector converte variante para vetor para cálculo de diversidade
func (fv *FunctionVariant) toVector() []float64 {
	// Simplificação: usar fitness e métricas como proxy
	return []float64{
		fv.Fitness,
		fv.ExecutionMetrics.AvgExecutionTimeMs,
		fv.ExecutionMetrics.AvgMemoryUsageMB,
		extractPhiCoherenceFromVariant(fv),
	}
}

// euclideanDistance calcula distância euclidiana entre vetores
func euclideanDistance(a, b []float64) float64 {
	if len(a) != len(b) {
		return math.MaxFloat64
	}
	sum := 0.0
	for i := range a {
		diff := a[i] - b[i]
		sum += diff * diff
	}
	return math.Sqrt(sum)
}

// Clone cria cópia profunda de FunctionVariant
func (fv *FunctionVariant) Clone() *FunctionVariant {
	clone := *fv
	clone.Operations = make([]EvolutionOp, len(fv.Operations))
	copy(clone.Operations, fv.Operations)
	clone.ExecutionMetrics = fv.ExecutionMetrics // Assumir struct copiável
	clone.CoSNARKProof = append([]byte(nil), fv.CoSNARKProof...)
	return &clone
}

// GetMetrics retorna métricas consolidadas da seleção
func (e *NaturalSelectionEngine) GetMetrics() SelectionMetrics {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.metrics
}

// GetBestVariant retorna a variante com melhor fitness atual
func (e *NaturalSelectionEngine) GetBestVariant() *FunctionVariant {
	e.mu.RLock()
	defer e.mu.RUnlock()

	if e.population == nil || len(e.population.Variants) == 0 {
		return nil
	}

	best := e.population.Variants[0]
	for _, v := range e.population.Variants[1:] {
		if v.Fitness > best.Fitness {
			best = v
		}
	}
	return best.Clone()
}
