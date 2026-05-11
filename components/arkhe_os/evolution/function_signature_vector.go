package evolution

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math"
	"time"
)

// ─── CONSTANTES DO ESPAÇO DE ASSINATURAS ─────────────────────────────

const (
	// SignatureVectorDim dimensão do vetor de assinatura
	SignatureVectorDim = 128

	// PhiTarget valor alvo da razão áurea para otimização
	PhiTarget = 1.618033988749895

	// MinPurityThreshold pureza mínima para considerar função "limpa"
	MinPurityThreshold = 0.7

	// MaxKolmogorovEst limite superior para estimativa de complexidade
	MaxKolmogorovEst = 1000.0
)

// ─── STUBS ─────────────────────────────────────────────────────────

type LFIRGraph struct {
	Nodes []*LFIRNode
}

type LFIRNode struct {
	ID         string
	Type       LFIRType
	Attributes map[string]interface{}
	Children   []*LFIRNode
	InputType  *TypeInfo
	OutputType *TypeInfo
}

type LFIRType string

const (
	LFIRIORead             LFIRType = "io_read"
	LFIRIOWrite            LFIRType = "io_write"
	LFIRMutate             LFIRType = "mutate"
	LFIRRand               LFIRType = "rand"
	LFIRTime               LFIRType = "time"
	LFIRConditional        LFIRType = "conditional"
	LFIROperation          LFIRType = "operation"
	LFIRFunctionCall       LFIRType = "function_call"
	LFIRRecursiveCall      LFIRType = "recursive_call"
	LFIRPureComputation    LFIRType = "pure_computation"
	LFIRSequence           LFIRType = "sequence"
	LFIRFusedOperation     LFIRType = "fused_operation"
	LFIRUnrolledRecursion  LFIRType = "unrolled_recursion"
	LFIRMemoizationWrapper LFIRType = "memoization_wrapper"
)

func (g *LFIRGraph) CanonicalHash() string                     { return "hash" }
func (g *LFIRGraph) Serialize() []byte                         { return []byte("serialized") }
func (g *LFIRGraph) MaxDepth() int                             { return 5 }
func (g *LFIRGraph) AvgBreadth() float64                       { return 2.5 }
func (g *LFIRGraph) NodeCount() int                            { return 10 }
func (g *LFIRGraph) EdgeCount() int                            { return 9 }
func (g *LFIRGraph) Clone() *LFIRGraph                         { return g }
func (g *LFIRGraph) SubgraphDepth(n *LFIRNode) int             { return 1 }
func (g *LFIRGraph) SubgraphSize(n *LFIRNode) int              { return 1 }
func (g *LFIRGraph) RecursionDepth(n *LFIRNode) int            { return 1 }
func (g *LFIRGraph) AccessFrequency(n *LFIRNode) int           { return 1 }
func (g *LFIRGraph) ReplaceNode(id string, new *LFIRNode)      {}
func (g *LFIRGraph) UpdateReferences(old, new string)          {}
func (g *LFIRGraph) GetFunction(name string) *LFIRGraph        { return nil }
func (g *LFIRGraph) CloneWithRenaming(prefix string) *LFIRNode { return nil }
func (g *LFIRGraph) ConnectIO(n, newN *LFIRNode)               {}
func (g *LFIRGraph) Size() int                                 { return len(g.Nodes) }

type TypeEmbedder struct{}

func GetTypeEmbedder() *TypeEmbedder                 { return &TypeEmbedder{} }
func (te *TypeEmbedder) Embed(name string) []float64 { return []float64{0.1, 0.2, 0.3, 0.4} }

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────────────────

// FunctionSignature representa a assinatura vetorial de uma função
type FunctionSignature struct {
	ID            string                      `json:"id"`             // Hash único da função
	Language      string                      `json:"language"`       // Linguagem original
	Library       string                      `json:"library"`        // Biblioteca de origem
	Name          string                      `json:"name"`           // Nome da função
	InputTypes    []TypeInfo                  `json:"input_types"`    // Tipos de entrada
	OutputTypes   []TypeInfo                  `json:"output_types"`   // Tipos de saída
	Vector        [SignatureVectorDim]float64 `json:"vector"`         // Vetor de assinatura
	Purity        float64                     `json:"purity"`         // [0,1] pureza funcional
	KolmogorovEst float64                     `json:"kolmogorov_est"` // Estimativa de complexidade
	PhiCoherence  float64                     `json:"phi_coherence"`  // [0,1] coerência φ
	LFIRHash      string                      `json:"lfir_hash"`      // Hash do grafo LFIR
	Timestamp     int64                       `json:"timestamp"`      // Unix timestamp
	Metadata      map[string]string           `json:"metadata"`       // Metadados extensíveis
}

// TypeInfo descreve um tipo no contexto da assinatura
type TypeInfo struct {
	Name        string            `json:"name"`        // Nome do tipo
	Kind        string            `json:"kind"`        // "primitive", "struct", "generic", etc.
	Constraints map[string]string `json:"constraints"` // Restrições de tipo (ex: "T: Comparable")
	Embedding   []float64         `json:"embedding"`   // Embedding semântico do tipo
}

// FunctionVariant representa uma variante evolutiva de uma função
type FunctionVariant struct {
	ParentID         string           `json:"parent_id"`         // ID da função original
	VariantID        string           `json:"variant_id"`        // ID único da variante
	Generation       int              `json:"generation"`        // Geração da evolução
	Operations       []EvolutionOp    `json:"operations"`        // Operações aplicadas
	Fitness          float64          `json:"fitness"`           // Score de fitness calculado
	ExecutionMetrics ExecutionMetrics `json:"execution_metrics"` // Métricas de execução reais
	CoSNARKProof     []byte           `json:"cosnark_proof"`     // Prova de preservação semântica
	Timestamp        int64            `json:"timestamp"`
}

// EvolutionOp enumera tipos de operações evolutivas
type EvolutionOp string

const (
	OpPhiRebalance    EvolutionOp = "phi_rebalance"    // Rebalancear estrutura por φ
	OpNodeFusion      EvolutionOp = "node_fusion"      // Fundir nós adjacentes
	OpSubgraphInline  EvolutionOp = "subgraph_inline"  // Inline de subgrafo
	OpRecursionUnroll EvolutionOp = "recursion_unroll" // Desenrolar recursão φ-vezes
	OpMemoizationAdd  EvolutionOp = "memoization_add"  // Adicionar cache φ-ótimo
	OpTypeSpecialize  EvolutionOp = "type_specialize"  // Especializar tipos genéricos
)

// ExecutionMetrics contém métricas de execução coletadas da Hyper-Mesh
type ExecutionMetrics struct {
	AvgExecutionTimeMs float64  `json:"avg_execution_time_ms"`
	P99ExecutionTimeMs float64  `json:"p99_execution_time_ms"`
	AvgMemoryUsageMB   float64  `json:"avg_memory_usage_mb"`
	P99MemoryUsageMB   float64  `json:"p99_memory_usage_mb"`
	EnergyCostEstimate float64  `json:"energy_cost_estimate"` // Estimativa em joules
	SuccessRate        float64  `json:"success_rate"`         // Taxa de execuções bem-sucedidas
	SampleCount        int64    `json:"sample_count"`         // Número de amostras coletadas
	NodesSampled       []string `json:"nodes_sampled"`        // IDs dos nós que coletaram métricas
}

// ─── CONSTRUTORES E MÉTODOS ─────────────────────────────────────────

// NewFunctionSignature cria nova assinatura a partir de grafo LFIR
func NewFunctionSignature(
	lfirGraph *LFIRGraph,
	language, library, name string,
	inputTypes, outputTypes []TypeInfo,
	metadata map[string]string,
) (*FunctionSignature, error) {
	// Gerar ID único baseado em hash do LFIR
	lfirHash := lfirGraph.CanonicalHash()
	sigID := sha256.Sum256([]byte(fmt.Sprintf("%s:%s:%s:%s", language, library, name, lfirHash)))

	// Calcular pureza: razão de nós sem efeitos colaterais
	purity := computePurity(lfirGraph)

	// Estimar complexidade de Kolmogorov via compressão do LFIR serializado
	kolmogorov := estimateKolmogorovComplexity(lfirGraph)

	// Calcular coerência φ: quão bem a estrutura do grafo ressoa com φ
	phiCoherence := computePhiCoherence(lfirGraph)

	// Gerar vetor de assinatura via embedding
	vector, err := generateSignatureVector(lfirGraph, inputTypes, outputTypes, purity, kolmogorov, phiCoherence)
	if err != nil {
		return nil, fmt.Errorf("failed to generate signature vector: %w", err)
	}

	return &FunctionSignature{
		ID:            hex.EncodeToString(sigID[:8]),
		Language:      language,
		Library:       library,
		Name:          name,
		InputTypes:    inputTypes,
		OutputTypes:   outputTypes,
		Vector:        vector,
		Purity:        purity,
		KolmogorovEst: kolmogorov,
		PhiCoherence:  phiCoherence,
		LFIRHash:      lfirHash,
		Timestamp:     time.Now().Unix(),
		Metadata:      metadata,
	}, nil
}

// computePurity calcula pureza funcional baseada em análise de efeitos colaterais
func computePurity(graph *LFIRGraph) float64 {
	totalNodes := len(graph.Nodes)
	if totalNodes == 0 {
		return 1.0
	}

	pureNodes := 0
	for _, node := range graph.Nodes {
		// Nó é puro se não tem efeitos colaterais conhecidos
		if !hasSideEffects(node) {
			pureNodes++
		}
	}

	return float64(pureNodes) / float64(totalNodes)
}

// hasSideEffects verifica se nó LFIR tem efeitos colaterais conhecidos
func hasSideEffects(node *LFIRNode) bool {
	// Lista de operações com efeitos colaterais conhecidos
	sideEffectOps := map[LFIRType]bool{
		LFIRIORead:  true,
		LFIRIOWrite: true,
		LFIRMutate:  true,
		LFIRRand:    true,
		LFIRTime:    true,
		// Adicionar conforme necessário
	}
	return sideEffectOps[node.Type]
}

// estimateKolmogorovComplexity estima complexidade via compressão do LFIR
func estimateKolmogorovComplexity(graph *LFIRGraph) float64 {
	// Serializar grafo para bytes
	serialized := graph.Serialize()
	originalSize := float64(len(serialized))

	// Comprimir via algoritmo simples (em produção: usar LZMA ou similar)
	compressed := compressSimple(serialized)
	compressedSize := float64(len(compressed))

	// Complexidade estimada: razão de compressão normalizada
	if originalSize == 0 {
		return 0
	}
	ratio := compressedSize / originalSize
	return math.Min(MaxKolmogorovEst, ratio*MaxKolmogorovEst)
}

// compressSimple implementa compressão básica para estimativa (placeholder)
func compressSimple(data []byte) []byte {
	// Em produção: usar biblioteca de compressão real
	// Aqui: simular compressão removendo bytes repetidos consecutivos
	if len(data) == 0 {
		return data
	}
	result := []byte{data[0]}
	for i := 1; i < len(data); i++ {
		if data[i] != data[i-1] {
			result = append(result, data[i])
		}
	}
	return result
}

// computePhiCoherence calcula quão bem a estrutura do grafo ressoa com φ
func computePhiCoherence(graph *LFIRGraph) float64 {
	// Analisar razões estruturais do grafo
	depth := graph.MaxDepth()
	breadth := graph.AvgBreadth()

	if breadth == 0 {
		return 0.5
	}

	// Calcular quão próximo depth/breadth está de φ
	ratio := float64(depth) / breadth
	deviation := math.Abs(ratio-PhiTarget) / PhiTarget

	// Mapear desvio para [0,1]: menor desvio = maior coerência
	coherence := math.Max(0, 1.0-deviation*2) // Penalizar desvios >50%
	return coherence
}

// generateSignatureVector gera vetor de assinatura via embeddings
func generateSignatureVector(
	graph *LFIRGraph,
	inputTypes, outputTypes []TypeInfo,
	purity, kolmogorov, phiCoherence float64,
) ([SignatureVectorDim]float64, error) {
	var vector [SignatureVectorDim]float64

	// Usar modelo de embeddings pré-treinado para tipos
	embedder := GetTypeEmbedder()

	// Embeddings de tipos de entrada (primeiros 32 dimensões)
	for i, t := range inputTypes {
		if i >= 8 {
			break
		} // Limitar a 8 tipos de entrada
		emb := embedder.Embed(t.Name)
		for j, v := range emb {
			if j >= 4 {
				break
			}
			vector[i*4+j] = v
		}
	}

	// Embeddings de tipos de saída (próximos 32 dimensões)
	for i, t := range outputTypes {
		if i >= 8 {
			break
		}
		emb := embedder.Embed(t.Name)
		for j, v := range emb {
			if j >= 4 {
				break
			}
			vector[32+i*4+j] = v
		}
	}

	// Métricas estruturais (próximos 32 dimensões)
	vector[64] = purity
	vector[65] = kolmogorov / MaxKolmogorovEst // Normalizar
	vector[66] = phiCoherence
	vector[67] = float64(graph.NodeCount()) / 1000.0 // Normalizar contagem de nós
	vector[68] = float64(graph.EdgeCount()) / 5000.0
	vector[69] = float64(graph.MaxDepth()) / 100.0

	// Hash estrutural como features adicionais (últimas 32 dimensões)
	hashBytes := sha256.Sum256([]byte(graph.CanonicalHash()))
	for i := 0; i < 32 && i < len(hashBytes); i++ {
		vector[SignatureVectorDim-32+i] = float64(hashBytes[i]) / 255.0
	}

	return vector, nil
}

// SimilarityTo calcula similaridade de cosseno entre assinaturas
func (fs *FunctionSignature) SimilarityTo(other *FunctionSignature) float64 {
	var dot, normA, normB float64
	for i := 0; i < SignatureVectorDim; i++ {
		a := fs.Vector[i]
		b := other.Vector[i]
		dot += a * b
		normA += a * a
		normB += b * b
	}
	if normA == 0 || normB == 0 {
		return 0
	}
	return dot / (math.Sqrt(normA) * math.Sqrt(normB))
}

// ComputeFitness calcula score de fitness baseado em métricas de execução
func (fv *FunctionVariant) ComputeFitness(weights map[string]float64) float64 {
	m := fv.ExecutionMetrics

	// Valores normalizados (menor é melhor para tempo/memória/energia)
	timeScore := 1.0 / (1.0 + m.AvgExecutionTimeMs/100.0) // Normalizar para ~[0,1]
	memoryScore := 1.0 / (1.0 + m.AvgMemoryUsageMB/500.0)
	energyScore := 1.0 / (1.0 + m.EnergyCostEstimate/10.0)

	// Coerência φ já está em [0,1]
	phiScore := extractPhiCoherenceFromVariant(fv)

	// Taxa de sucesso como multiplicador
	successMultiplier := 0.5 + 0.5*m.SuccessRate // Mapear [0,1] → [0.5,1.0]

	// Combinação ponderada
	fitness := weights["time"]*timeScore +
		weights["memory"]*memoryScore +
		weights["energy"]*energyScore +
		weights["phi"]*phiScore

	return fitness * successMultiplier
}

// extractPhiCoherenceFromVariant extrai coerência φ dos metadados da variante
func extractPhiCoherenceFromVariant(fv *FunctionVariant) float64 {
	// Em produção: extrair do LFIR da variante
	// Aqui: valor placeholder baseado em operações aplicadas
	basePhi := 0.7
	for _, op := range fv.Operations {
		if op == OpPhiRebalance {
			basePhi += 0.1
		}
	}
	return math.Min(1.0, basePhi)
}
