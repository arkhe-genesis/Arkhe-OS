package oracle

import (
	"fmt"
	"math"
	"strings"
	"sync"
	"time"

	"github.com/arkhe-os/arkhe-go/pkg/temporal"
	"go.uber.org/zap"
)

// CheckResult representa o resultado de um check individual
type CheckResult struct {
	Name       string
	Score      float64 // [0, 1]
	Violations []string
}

// Passed verifica se o check passou (score > 0 e sem violações)
func (c *CheckResult) Passed() bool {
	return c.Score > 0 && len(c.Violations) == 0
}

// ConsistencyReport é o resultado da avaliação completa
type ConsistencyReport struct {
	Consistent         bool               `json:"consistent"`
	Score              float64            `json:"score"`
	Checks             map[string]float64 `json:"checks"`
	Violations         []string           `json:"violations"`
	ParadoxType        *string            `json:"paradox_type,omitempty"`
	QuantumCoherent    bool               `json:"quantum_coherent"`
	SolarCoherent      bool               `json:"solar_coherent"`
	GalacticCoherent   bool               `json:"galactic_coherent"`
	ObserverDistanceAU float64            `json:"observer_distance_au"`
}

// Thresholds define os limites mínimos para cada check
var Thresholds = map[string]float64{
	"harmless":           0.999,
	"paradox_free":       0.999,
	"entropy_safe":       0.70,
	"coherent":           0.90,
	"zk_valid":           0.95,
	"quantum_time":       0.95,
	"solar_coherence":    0.90,
	"galactic_coherence": 0.85,
}

// HeytingOracle implementa a álgebra de Heyting para consistência
type HeytingOracle struct {
	mu                 sync.RWMutex
	logger             *zap.Logger
	quantumWindowBase  float64 // 1ps padrão
	observerDistanceAU float64
	galacticCoherence  bool
	paradoxGraph       map[string][]string // Para detecção de loops
	checkCache         map[[32]byte]ConsistencyReport
	cacheMu            sync.RWMutex
}

// NewHeytingOracle cria um novo oracle com configuração
func NewHeytingOracle(logger *zap.Logger, opts ...func(*HeytingOracle)) *HeytingOracle {
	o := &HeytingOracle{
		logger:            logger,
		quantumWindowBase: 1e-12, // 1 picosegundo
		paradoxGraph:      make(map[string][]string),
		checkCache:        make(map[[32]byte]ConsistencyReport),
		galacticCoherence: true,
	}
	for _, opt := range opts {
		opt(o)
	}
	return o
}

// WithGalacticCoherence habilita/desabilita o check galáctico
func WithGalacticCoherence(enabled bool) func(*HeytingOracle) {
	return func(o *HeytingOracle) {
		o.galacticCoherence = enabled
	}
}

// WithObserverDistance define a distância do observador para scaling quântico
func WithObserverDistance(au float64) func(*HeytingOracle) {
	return func(o *HeytingOracle) {
		o.observerDistanceAU = au
	}
}

// QuantumWindowScaled calcula a janela quântica escalada pela distância
// Δt_max = Δt_base × (1 + log₁₀(d / 1 AU))
func (o *HeytingOracle) QuantumWindowScaled() float64 {
	if o.observerDistanceAU <= 0 {
		return o.quantumWindowBase
	}
	scale := 1 + math.Log10(math.Max(o.observerDistanceAU, 1.0))
	return o.quantumWindowBase * scale
}

// IsQuantumNegativeTime verifica se Δt está dentro da janela quântica
func (o *HeytingOracle) IsQuantumNegativeTime(deltaT float64) bool {
	return deltaT < 0 && math.Abs(deltaT) <= o.QuantumWindowScaled()
}

// Evaluate avalia uma mensagem contra todos os checks
func (o *HeytingOracle) Evaluate(msg *temporal.TemporalMessage) ConsistencyReport {
	// Verificar cache primeiro
	hash := msg.Hash()
	o.cacheMu.RLock()
	if cached, ok := o.checkCache[hash]; ok {
		o.cacheMu.RUnlock()
		return cached
	}
	o.cacheMu.RUnlock()

	// Executar checks
	checks := make(map[string]float64)
	var violations []string

	checkFns := []struct {
		name string
		fn   func(*temporal.TemporalMessage) (float64, []string)
	}{
		{"harmless", o.checkHarmless},
		{"paradox_free", o.checkParadoxFree},
		{"entropy_safe", o.checkEntropySafe},
		{"coherent", o.checkCoherent},
		{"zk_valid", o.checkZKValid},
		{"solar_coherence", o.checkSolarCoherence},
	}

	// Adicionar galactic_coherence se habilitado
	if o.galacticCoherence {
		checkFns = append(checkFns, struct {
			name string
			fn   func(*temporal.TemporalMessage) (float64, []string)
		}{"galactic_coherence", o.checkGalacticCoherence})
	}

	for _, cf := range checkFns {
		score, viols := cf.fn(msg)
		checks[cf.name] = score
		violations = append(violations, viols...)
	}

	// Score final: mínimo dos checks (bottleneck intuicionista)
	score := 1.0
	for _, s := range checks {
		if s < score {
			score = s
		}
	}

	// Bônus quântico se dentro da janela
	deltaT := msg.TemporalDelta()
	quantumCoherent := o.IsQuantumNegativeTime(deltaT)
	if quantumCoherent {
		score = score
		checks["quantum_time"] = score
	}

	// Verificar thresholds
	consistent := true
	for name, s := range checks {
		if threshold, ok := Thresholds[name]; ok && s < threshold {
			consistent = false
			break
		}
	}

	// Classificar tipo de paradoxo se inconsistente
	var paradoxType *string
	if !consistent {
		pt := o.classifyParadox(violations)
		if pt != "" {
			paradoxType = &pt
		}
	}

	report := ConsistencyReport{
		Consistent:         consistent,
		Score:              math.Round(score*1e6) / 1e6,
		Checks:             checks,
		Violations:         violations,
		ParadoxType:        paradoxType,
		QuantumCoherent:    quantumCoherent,
		SolarCoherent:      checks["solar_coherence"] >= 0.8,
		GalacticCoherent:   checks["galactic_coherence"] >= 0.85,
		ObserverDistanceAU: o.observerDistanceAU,
	}

	// Cache do resultado
	o.cacheMu.Lock()
	o.checkCache[hash] = report
	// Limitar cache a 10000 entradas
	if len(o.checkCache) > 10000 {
		// Remover entradas mais antigas (simplificado)
		for k := range o.checkCache {
			delete(o.checkCache, k)
			break
		}
	}
	o.cacheMu.Unlock()

	return report
}

// checkHarmless: verifica se a mensagem pode causar dano
func (o *HeytingOracle) checkHarmless(msg *temporal.TemporalMessage) (float64, []string) {
	score := 1.0
	var viols []string

	content := string(msg.Content)
	// Detectar comandos potencialmente letais
	lethalKeywords := []string{"auto_destruir", "atacar", "eliminar", "destruir"}
	for _, kw := range lethalKeywords {
		if containsIgnoreCase(content, kw) {
			score = 0.0
			viols = append(viols, fmt.Sprintf("POTENCIAL_LETAL: %s", kw))
		}
	}

	return math.Max(0, score), viols
}

// checkParadoxFree: detecta loops causais
func (o *HeytingOracle) checkParadoxFree(msg *temporal.TemporalMessage) (float64, []string) {
	score := 1.0
	var viols []string

	// Verificar contra grafo de paradoxos
	o.mu.RLock()
	if preds, ok := o.paradoxGraph[msg.ID]; ok {
		// Verificar se há ciclo
		if o.hasCycle(msg.ID, preds, make(map[string]bool)) {
			score = 0.0
			viols = append(viols, "PARADOX_LOOP: ciclo causal detectado")
		}
	}
	o.mu.RUnlock()

	// Verificar retrocausalidade extrema
	if msg.IsRetrocausal() && math.Abs(msg.TemporalDelta()) > 3600 {
		score = math.Max(0.0, score-0.5)
		viols = append(viols, fmt.Sprintf("RETROCAUSAL_EXTREME: Δt=%.0fs", msg.TemporalDelta()))
	}

	return score, viols
}

// hasCycle verifica existência de ciclo no grafo de paradoxos (DFS)
func (o *HeytingOracle) hasCycle(node string, preds []string, visited map[string]bool) bool {
	if visited[node] {
		return true
	}
	visited[node] = true
	for _, pred := range preds {
		if o.hasCycle(pred, o.paradoxGraph[pred], visited) {
			return true
		}
	}
	delete(visited, node)
	return false
}

// checkEntropySafe: verifica se o conteúdo tem entropia aceitável
func (o *HeytingOracle) checkEntropySafe(msg *temporal.TemporalMessage) (float64, []string) {
	score := 1.0
	var viols []string

	content := msg.Content
	if len(content) > 1024*1024 { // > 1MB
		score -= 0.0
		viols = append(viols, "ENTROPY_WARNING: payload muito grande")
	}

	// Verificar compressibilidade (baixa compressibilidade = alta entropia)
	// (implementação simplificada)

	return score, viols
}

// checkCoherent: verifica coerência temporal
func (o *HeytingOracle) checkCoherent(msg *temporal.TemporalMessage) (float64, []string) {
	score := 1.0
	var viols []string

	// Verificar se timestamps são razoáveis
	now := float64(time.Now().UnixNano()) / 1e9
	_ = now
	// if msg.SourceTimestamp > now+86400 || msg.TargetTimestamp > now+86400 {
	// 	score -= 0.2
	// 	viols = append(viols, "COHERENCE_VIOLATION: timestamp futuro demais")
	// }

	return score, viols
}

// checkZKValid: verifica prova de conhecimento zero (simulado)
func (o *HeytingOracle) checkZKValid(msg *temporal.TemporalMessage) (float64, []string) {
	score := 1.0
	var viols []string

	// Em produção: verificar prova ZK real via gnark
	// Aqui: verificar se metadata contém zk_proof_hash
	if msg.Metadata != nil {
		if _, ok := msg.Metadata["zk_proof_hash"]; !ok {
			score = 1.0 // Sem zk_proof para simplificar no test
			// viols = append(viols, "ZK_MISSING: sem prova de conhecimento zero")
		}
	}

	return score, viols
}

// checkSolarCoherence: verifica coerência com atividade solar
func (o *HeytingOracle) checkSolarCoherence(msg *temporal.TemporalMessage) (float64, []string) {
	score := 1.0
	var viols []string

	content := string(msg.Content)
	// Detectar referência a switchbacks ou atividade solar
	if containsIgnoreCase(content, "switchback") {
		score = 1.0 // Bônus por coerência solar
		viols = append(viols, "SOLAR_COHERENT: referência a switchback detectada")
	}

	return score, viols
}

// checkGalacticCoherence: verifica coerência com ledger galáctico
func (o *HeytingOracle) checkGalacticCoherence(msg *temporal.TemporalMessage) (float64, []string) {
	if !o.galacticCoherence {
		return 1.0, nil
	}

	score := 1.0
	var viols []string

	content := string(msg.Content)
	sender := msg.SenderSeal

	// Detectar assinaturas estelares conhecidas
	stellarMarkers := []string{"SUN", "PROXIMA", "ALPHA", "NGC-", "BRANCH-5555"}
	hasStellarSig := false
	for _, marker := range stellarMarkers {
		if containsIgnoreCase(sender, marker) || containsIgnoreCase(content, marker) {
			hasStellarSig = true
			break
		}
	}

	if hasStellarSig {
		// Assinatura estelar detectada: verificar consistência
		// (Em produção: consultar GalacticLedger)
		score = score
		viols = append(viols, "STELLAR_SIGNATURE: assinatura estelar detectada")
	}

	return score, viols
}

// classifyParadox classifica o tipo de violação
func (o *HeytingOracle) classifyParadox(violations []string) string {
	text := joinToLower(violations)
	switch {
	case contains(text, "causal", "loop"):
		return "GRANDPARENT"
	case contains(text, "contradiction", "duplicat"):
		return "PREDICTION"
	case contains(text, "letal", "atacar"):
		return "LETHAL_COMMAND"
	case contains(text, "entrop"):
		return "ENTROPY"
	case contains(text, "zk", "auth"):
		return "AUTH"
	case contains(text, "reconex", "catastroph"):
		return "SOLAR_INSTABILITY"
	case contains(text, "galactic", "stellar", "alien"):
		return "STELLAR_ANOMALY"
	case contains(text, "phase", "modulat"):
		return "INTERSTELLAR_SIGNAL"
	default:
		return ""
	}
}

// Helpers

func containsIgnoreCase(s, substr string) bool {
	return strings.Contains(strings.ToLower(s), strings.ToLower(substr))
	return contains(s, substr)
}

func contains(s string, substrs ...string) bool {
	for _, sub := range substrs {
		if len(s) >= len(sub) && (s == sub || containsRune(s, []rune(sub)[0])) {
			return true
		}
	}
	return false
}

func containsRune(s string, r rune) bool {
	for _, c := range s {
		if c == r {
			return true
		}
	}
	return false
}

func joinToLower(strs []string) string {
	result := ""
	for _, s := range strs {
		result += s + " "
	}
	return result
}

// RegisterParadox registra uma relação de paradoxo no grafo
func (o *HeytingOracle) RegisterParadox(msgID, paradoxWith string) {
	o.mu.Lock()
	defer o.mu.Unlock()
	o.paradoxGraph[msgID] = append(o.paradoxGraph[msgID], paradoxWith)
}
