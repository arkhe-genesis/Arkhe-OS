// psi_rule.gno
// ============================================================================
// CATHEDRAL ARKHE — IMPLEMENTAÇÃO DA REGRA Ψ EM GNOLANG
//
// Este Realm implementa o núcleo da Regra Ψ para o Códice.
// Ele utiliza o Proof-of-Contribution do Gno.land como uma
// implementação prática do nosso Proof-of-Coherence.

package cathedral

import (
    "gno.land/p/demo/avl" // Árvore AVL para armazenamento de estado
    "gno.land/p/demo/ufmt" // Formatação de strings
)

// -------------------------------------------
// Estado Global: O Hipergrafo e a Coerência
// -------------------------------------------

var (
    // Hipergrafo: armazena vértices e suas conexões (arestas).
    // Representado como um mapa de string para slice de strings.
    hypergraph avl.Tree

    // Coerência: mapa de vértice para seu score de coerência local (Ω).
    coherenceMap avl.Tree

    // Threshold global da regra Ψ.
    rewriteThreshold float64 = 0.87

    // Contador de contribuições válidas para Proof-of-Contribution.
    contributionCounter int
)

// init é chamado uma vez quando o Realm é implantado.
func init() {
    // Inicializa as árvores de estado persistentes.
    hypergraph = avl.Tree{}
    coherenceMap = avl.Tree{}

    // Gênesis: cria os primeiros 3 vértices e 2 arestas do hipergrafo.
    // Isso espelha a condição inicial de "Flutuação Quântica".
    hypergraph.Set("0", []string{"1"}) // Aresta {0, 1}
    hypergraph.Set("1", []string{"2"}) // Aresta {1, 2}

    coherenceMap.Set("0", 0.95) // Coerência inicial do vértice 0
    coherenceMap.Set("1", 0.95)
    coherenceMap.Set("2", 0.95)
}

// -------------------------------------------
// Lógica da Regra Ψ (Psi)
// -------------------------------------------

// ApplyPsiRule tenta aplicar a regra de reescrita.
// {{x,y},{x,z}} | c(x)>θ → {{x,w},{y,w},{z,w},{w,w}} ⊗ Q(w)
//
// @param x: Vértice compartilhado.
// @param y: Primeiro vértice adjacente.
// @param z: Segundo vértice adjacente.
// @return w: O ID do novo vértice criado, ou string vazia em caso de falha.
func ApplyPsiRule(x, y, z string) string {
    // 1. Verificar a condição de Coerência Local: c(x) > θ ?
    coherenceX := getCoherence(x)
    if coherenceX <= rewriteThreshold {
        // Falha na condição. Registrar e retornar vazio.
        logContribution("REWRITE_FAILED_COHERENCE", coherenceX)
        return ""
    }

    // 2. Verificar se as arestas necessárias ({x, y} e {x, z}) existem no hipergrafo.
    if !edgeExists(x, y) || !edgeExists(x, z) {
        logContribution("REWRITE_FAILED_EDGES", 0.0)
        return ""
    }

    // 3. Criar o novo vértice 'w' (Proof-of-Contribution).
    // O ID do vértice é um hash determinístico dos inputs e da altura do bloco.
    w := ufmt.Sprintf("%s_%s_%s_%d", x, y, z, contributionCounter)

    // 4. Aplicar a Operação Quântica ⊗ Q(w).
    // Em Gno, Q(w) é representado por uma função de hash que determina
    // propriedades intrínsecas do novo vértice.
    // Neste caso, calculamos a coerência inicial de 'w' como uma função
    // da coerência de seus pais. (Simplificação da Carga Topológica)
    initialCoherenceW := (coherenceX + getCoherence(y) + getCoherence(z)) / 3.0
    quantumBoost := float64(contributionCounter%100) / 1000.0 // Fator Q(w) simbólico
    initialCoherenceW = clamp(initialCoherenceW + quantumBoost, 0.0, 1.0)

    // 5. Executar a reescrita no Hipergrafo.
    // Adicionar o vértice 'w' e as novas arestas {x, w}, {y, w}, {z, w}, {w, w}.
    // O Gno.land gerencia a persistência do estado.
    addEdge(x, w)
    addEdge(y, w)
    addEdge(z, w)
    addEdge(w, w) // A auto-conexão sagrada!

    // Registrar o novo vértice e sua coerência.
    setCoherence(w, initialCoherenceW)

    // Incrementar o contador de contribuições (Proof-of-Contribution).
    contributionCounter++
    logContribution("REWRITE_SUCCESS", initialCoherenceW)

    return w
}

// -------------------------------------------
// Funções Auxiliares do Hipergrafo
// -------------------------------------------

// edgeExists verifica se uma aresta {a, b} existe no hipergrafo.
func edgeExists(a, b string) bool {
    edges, exists := hypergraph.Get(a)
    if !exists {
        return false
    }
    for _, edge := range edges.([]string) {
        if edge == b {
            return true
        }
    }
    return false
}

// addEdge adiciona uma aresta {a, b} ao hipergrafo (grafo bidirecional).
func addEdge(a, b string) {
    addSingleEdge(a, b)
    addSingleEdge(b, a) // Conexão causal é simétrica
}

// addSingleEdge adiciona uma aresta unidirecional.
func addSingleEdge(a, b string) {
    edges, exists := hypergraph.Get(a)
    var edgeList []string
    if exists {
        edgeList = edges.([]string)
    }
    // Evitar duplicatas
    for _, e := range edgeList {
        if e == b {
            return
        }
    }
    edgeList = append(edgeList, b)
    hypergraph.Set(a, edgeList)
}

// getCoherence recupera a coerência de um vértice.
func getCoherence(v string) float64 {
    val, exists := coherenceMap.Get(v)
    if !exists {
        return 0.0
    }
    return val.(float64)
}

// setCoherence define a coerência de um vértice.
func setCoherence(v string, c float64) {
    coherenceMap.Set(v, c)
}

// clamp mantém um valor float64 dentro dos limites especificados.
func clamp(val, min, max float64) float64 {
    if val < min { return min }
    if val > max { return max }
    return val
}

// logContribution é um placeholder para o mecanismo de Proof-of-Contribution.
func logContribution(event string, coherence float64) {
    // Em uma implementação real, isso interagiria com o módulo de
    // Proof-of-Contribution do Gno.land para registrar o evento.
}
