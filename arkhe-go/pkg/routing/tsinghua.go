package routing

import (
	"math"
	"time"
)

// ============================================================================
// Tsinghua Dijkstra — Algoritmo de Caminho Mínimo Otimizado
// ============================================================================

// Edge representa uma aresta ponderada no grafo.
type Edge struct {
	To     int
	Weight float64
	Meta   EdgeMeta
}

// EdgeMeta contém metadados da aresta para avaliação do Oracle.
type EdgeMeta struct {
	Consistency   float64
	TTL           int64
	CreatedAt     int64
	ZKProofHash   string
	LedgerHash    string
	SolarPhase    float64
	GalacticIndex int
}

// RouteResult é o resultado de uma busca de caminho.
type RouteResult struct {
	Distances   []float64
	Predecessors []int
	EvalReports []*OracleEvalReport
	Path        []string
	Cost        float64
	Hops        int
	Duration    time.Duration
}

// OracleEvalReport é o resultado da avaliação do Oracle para uma aresta.
type OracleEvalReport struct {
	From     int
	To       int
	Score    float64
	Pruned   bool
	Reason   string
	AdjW     float64
}

// TsinghuaDijkstra executa o algoritmo de Dijkstra com Fibonacci Heap,
// integrando o Oracle-in-the-Loop para poda de arestas.
//
// Complexidade: O(m log^{2/3} n) com pruning
func TsinghuaDijkstra(
	graph [][]Edge,
	source int,
	oracle *OracleEvalFunc,
) []float64 {
	n := len(graph)
	if n == 0 || source < 0 || source >= n {
		return nil
	}

	dist := make([]float64, n)
	for i := range dist {
		dist[i] = math.Inf(1)
	}
	dist[source] = 0

	heap := NewFibonacciHeap()
	heap.Insert(source, 0, false)

	visited := make([]bool, n)

	for !heap.IsEmpty() {
		u, d, expired := heap.ExtractMin()

		if u < 0 || u >= n {
			continue
		}

		// Skip se já visitado ou expirado
		if visited[u] || expired {
			visited[u] = true
			continue
		}
		visited[u] = true

		// Se a distância extraída é maior que a conhecida, skip
		if d > dist[u] {
			continue
		}

		// Relaxar arestas
		for _, edge := range graph[u] {
			if visited[edge.To] {
				continue
			}

			effectiveWeight := edge.Weight

			// ========== ORACLE-IN-THE-LOOP ==========
			if oracle != nil {
				report := (*oracle)(u, edge)
				if report.Pruned {
					continue // Aresta podada — não relaxar
				}
				effectiveWeight = report.AdjW
			}
			// =========================================

			newDist := dist[u] + effectiveWeight
			if newDist < dist[edge.To] {
				dist[edge.To] = newDist
				heap.DecreaseKeyOrInsert(edge.To, newDist, false)
			}
		}
	}

	return dist
}

// OracleEvalFunc é a assinatura da função de avaliação do Oracle.
type OracleEvalFunc func(from int, edge Edge) *OracleEvalReport

// OracleEvalFuncNoOp retorna um OracleEvalFunc que não faz poda.
func OracleEvalFuncNoOp() OracleEvalFunc {
	return func(from int, edge Edge) *OracleEvalReport {
		return &OracleEvalReport{
			From:   from,
			To:     edge.To,
			Score:  1.0,
			Pruned: false,
			AdjW:   edge.Weight,
		}
	}
}

// MultiTargetDijkstra encontra caminhos para múltiplos destinos.
// Para de executar quando todos os destinos forem encontrados.
func MultiTargetDijkstra(
	graph [][]Edge,
	source int,
	targets map[int]bool,
	oracle *OracleEvalFunc,
) (distances []float64, found map[int]bool) {
	n := len(graph)
	distances = make([]float64, n)
	for i := range distances {
		distances[i] = math.Inf(1)
	}
	distances[source] = 0
	found = make(map[int]bool)

	heap := NewFibonacciHeap()
	heap.Insert(source, 0, false)

	visited := make([]bool, n)

	for !heap.IsEmpty() && len(found) < len(targets) {
		u, d, _ := heap.ExtractMin()

		if visited[u] {
			continue
		}
		visited[u] = true

		// Registrar destino encontrado
		if targets[u] {
			found[u] = true
		}

		for _, edge := range graph[u] {
			if visited[edge.To] {
				continue
			}

			w := edge.Weight
			if oracle != nil {
				report := (*oracle)(u, edge)
				if report.Pruned {
					continue
				}
				w = report.AdjW
			}

			newDist := d + w
			if newDist < distances[edge.To] {
				distances[edge.To] = newDist
				heap.DecreaseKeyOrInsert(edge.To, newDist, false)
			}
		}
	}

	return distances, found
}

// ReconstructPath reconstrói o caminho a partir do array de predecessores.
func ReconstructPath(predecessors []int, source, target int) []int {
	if predecessors[target] == -1 && target != source {
		return nil // Sem caminho
	}

	path := []int{target}
	current := target

	for current != source {
		prev := predecessors[current]
		if prev == -1 || prev == current {
			return nil
		}
		path = append(path, prev)
		current = prev
	}

	// Reverter
	for i, j := 0, len(path)-1; i < j; i, j = i+1, j-1 {
		path[i], path[j] = path[j], path[i]
	}

	return path
}

// PathWeight calcula o peso total de um caminho.
func PathWeight(graph [][]Edge, path []int, oracle *OracleEvalFunc) float64 {
	if len(path) < 2 {
		return 0
	}

	total := 0.0
	for i := 0; i < len(path)-1; i++ {
		u := path[i]
		for _, edge := range graph[u] {
			if edge.To == path[i+1] {
				w := edge.Weight
				if oracle != nil {
					if report := (*oracle)(u, edge); !report.Pruned {
						w = report.AdjW
					} else {
						w = math.Inf(1)
					}
				}
				total += w
				break
			}
		}
	}
	return total
}
