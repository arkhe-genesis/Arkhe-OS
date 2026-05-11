package consensus

import (
	"math"
	"sync"
	"time"
	"fmt"

	arkhecore "github.com/arkhe-os/arkhe-go/pkg/core"
)

// ============================================================================
// Tipos Fundamentais do Oracle
// ============================================================================

// Score é um valor de verdade intuicionista no intervalo [0, 1].
type Score float64

// Verdade topo (⊤)
const ScoreTop Score = 1.0

// Falso bottom (⊥)
const ScoreBottom Score = 0.0

// CheckName é o nome de um check de consistência.
type CheckName string

const (
	CheckHarmless       CheckName = "harmless"
	CheckParadoxFree    CheckName = "paradox_free"
	CheckEntropySafe    CheckName = "entropy_safe"
	CheckCoherent       CheckName = "coherent"
	CheckZKValid        CheckName = "zk_valid"
	CheckQuantumTime    CheckName = "quantum_time"
	CheckSolarCoherence CheckName = "solar_coherence"
	CheckGalacticAuth   CheckName = "galactic_coherence"
)

// Todos os checks na ordem de importância
var AllChecks = []CheckName{
	CheckParadoxFree,
	CheckHarmless,
	CheckCoherent,
	CheckZKValid,
	CheckQuantumTime,
	CheckSolarCoherence,
	CheckGalacticAuth,
	CheckEntropySafe,
}

// ============================================================================
// Resultado de um Check Individual
// ============================================================================

// CheckResult é o resultado de um único check.
type CheckResult struct {
	Name      CheckName
	Score     Score
	Violations []string
	Passes    bool
}

// NewCheckResult cria um novo resultado de check.
func NewCheckResult(name CheckName, score Score, violations ...string) *CheckResult {
	return &CheckResult{
		Name:       name,
		Score:      clampScore(score),
		Violations: violations,
		Passes:     len(violations) == 0 && score > 0,
	}
}

func clampScore(s Score) Score {
	if s < 0 {
		return 0
	}
	if s > 1 {
		return 1
	}
	return s
}

// ============================================================================
// Thresholds (Valores de Corte por Check)
// ============================================================================

// Thresholds define os limites mínimos para cada tipo de check.
type Thresholds struct {
	Harmless      Score // Rota não pode causar dano
	ParadoxFree   Score // Zero tolerância a paradoxos
	EntropySafe   Score // Entropia aceitável
	Coherent      Score // Coerência temporal mínima
	ZKValid       Score // Prova ZK válida
	QuantumTime   Score // Consistência quântica temporal
	SolarCoherence Score // Coerência com o Sol
	GalacticAuth   Score // Coerência com o Ledger Galáctico
}

// DefaultThresholds retorna os thresholds padrão.
func DefaultThresholds() *Thresholds {
	return &Thresholds{
		Harmless:       0.90,
		ParadoxFree:    0.95,
		EntropySafe:    0.70,
		Coherent:       0.85,
		ZKValid:        0.80,
		QuantumTime:    0.95,
		SolarCoherence: 0.60,
		GalacticAuth:   0.50,
	}
}

// ParanoidThresholds retorna os thresholds mais rigorosos.
func ParanoidThresholds() *Thresholds {
	return &Thresholds{
		Harmless:       0.999,
		ParadoxFree:    0.999,
		EntropySafe:    0.80,
		Coherent:       0.95,
		ZKValid:        0.95,
		QuantumTime:    0.95,
		SolarCoherence: 0.90,
		GalacticAuth:   0.85,
	}
}

func (t *Thresholds) Get(name CheckName) Score {
	switch name {
	case CheckHarmless:
		return t.Harmless
	case CheckParadoxFree:
		return t.ParadoxFree
	case CheckEntropySafe:
		return t.EntropySafe
	case CheckCoherent:
		return t.Coherent
	case CheckZKValid:
		return t.ZKValid
	case CheckQuantumTime:
		return t.QuantumTime
	case CheckSolarCoherence:
		return t.SolarCoherence
	case CheckGalacticAuth:
		return t.GalacticAuth
	default:
		return 0
	}
}

// ============================================================================
// Pesos Relativos (Importância de cada check)
// ============================================================================

// CheckWeights define a importância relativa de cada check.
type CheckWeights struct {
	Harmless       float64
	ParadoxFree    float64
	EntropySafe    float64
	Coherent       float64
	ZKValid        float64
	QuantumTime    float64
	SolarCoherence float64
	GalacticAuth   float64
}

// DefaultWeights retorna os pesos padrão.
func DefaultWeights() *CheckWeights {
	return &CheckWeights{
		Harmless:       2.0,
		ParadoxFree:    3.0,
		EntropySafe:    1.0,
		Coherent:       1.5,
		ZKValid:        1.0,
		QuantumTime:    1.2,
		SolarCoherence: 0.5,
		GalacticAuth:   0.5,
	}
}

func (w *CheckWeights) Get(name CheckName) float64 {
	switch name {
	case CheckHarmless:
		return w.Harmless
	case CheckParadoxFree:
		return w.ParadoxFree
	case CheckEntropySafe:
		return w.EntropySafe
	case CheckCoherent:
		return w.Coherent
	case CheckZKValid:
		return w.ZKValid
	case CheckQuantumTime:
		return w.QuantumTime
	case CheckSolarCoherence:
		return w.SolarCoherence
	case CheckGalacticAuth:
		return w.GalacticAuth
	default:
		return 1.0
	}
}

// ============================================================================
// Consistency Report
// ============================================================================

// ConsistencyReport é o resultado completo da avaliação do Oracle.
type ConsistencyReport struct {
	MessageID        string           `json:"message_id"`
	Score            Score            `json:"score"`
	AdjustedWeight   float64          `json:"adjusted_weight"`
	Pruned           bool             `json:"pruned"`
	PruneReason      string           `json:"prune_reason,omitempty"`
	Checks           map[CheckName]*CheckResult `json:"checks"`
	TemporalIndex    int              `json:"temporal_index"`
	EvaluatedAt      int64            `json:"evaluated_at"`
	ParadoxDetected  bool             `json:"paradox_detected"`
	QuantumAnomaly   bool             `json:"quantum_anomaly"`
}

// NewConsistencyReport cria um novo relatório.
func NewConsistencyReport(msgID string) *ConsistencyReport {
	return &ConsistencyReport{
		MessageID:     msgID,
		Score:         ScoreTop,
		AdjustedWeight: 1.0,
		Checks:         make(map[CheckName]*CheckResult),
		EvaluatedAt:    time.Now().UnixNano(),
	}
}

// IsConsistent retorna true se o score atende ao threshold.
func (r *ConsistencyReport) IsConsistent(threshold Score) bool {
	return r.Score >= threshold && !r.Pruned
}

// EffectiveWeight retorna o peso ajustado pelo Oracle.
func (r *ConsistencyReport) EffectiveWeight(rawWeight float64) float64 {
	if r.Pruned {
		return math.Inf(1)
	}
	return rawWeight / float64(max(r.Score, 0.001))
}

// ============================================================================
// Contexto de Avaliação (Caminho Atual)
// ============================================================================

// EvalContext contém o contexto da avaliação (caminho percorrido).
type EvalContext struct {
	Visited         map[arkhecore.Address]bool
	TemporalIndex   int
	PathLength      int
	AccumulatedCost float64
	MinScore        Score
}

// NewEvalContext cria um novo contexto de avaliação.
func NewEvalContext() *EvalContext {
	return &EvalContext{
		Visited: make(map[arkhecore.Address]bool),
		MinScore: ScoreTop,
	}
}

// VisitedContains verifica se o nó já foi visitado.
func (c *EvalContext) VisitedContains(addr arkhecore.Address) bool {
	return c.Visited[addr]
}

// VisitedAdd marca um nó como visitado.
func (c *EvalContext) VisitedAdd(addr arkhecore.Address) {
	c.Visited[addr] = true
	c.TemporalIndex++
}

// ============================================================================
// Consistency Oracle
// ============================================================================

// ConsistencyOracle avalia se uma mensagem é causalmente consistente.
// Implementa uma álgebra de Heyting: cada check é um morfismo no
// reticulado de Heyting dos scores de consistência.
type ConsistencyOracle struct {
	thresholds *Thresholds
	weights    *CheckWeights
	strictMode bool
	solarModel SolarCoherenceChecker

	// Estatísticas
	mu          sync.RWMutex
	evaluations uint64
	pruned      uint64
	accepted    uint64
}

// ConsistencyOracleConfig é a configuração do Oracle.
type ConsistencyOracleConfig struct {
	Thresholds     *Thresholds
	Weights        *CheckWeights
	StrictMode     bool
	EnableSolar    bool
	EnableGalactic bool
}

// NewConsistencyOracle cria um novo ConsistencyOracle.
func NewConsistencyOracle(cfg *ConsistencyOracleConfig) *ConsistencyOracle {
	if cfg == nil {
		cfg = &ConsistencyOracleConfig{}
	}

	thresholds := cfg.Thresholds
	if thresholds == nil {
		thresholds = DefaultThresholds()
	}

	weights := cfg.Weights
	if weights == nil {
		weights = DefaultWeights()
	}

	return &ConsistencyOracle{
		thresholds: thresholds,
		weights:    weights,
		strictMode: cfg.StrictMode,
	}
}

// RegisterSolarModel registra um modelo de coerência solar.
func (o *ConsistencyOracle) RegisterSolarModel(model SolarCoherenceChecker) {
	o.solarModel = model
}

// Evaluate avalia a consistência de uma mensagem.
// Esta é a operação central do Oracle — equivalente à avaliação da
// álgebra de Heyting sobre o conjunto de proposições temporais.
func (o *ConsistencyOracle) Evaluate(
	msg *arkhecore.TemporalMessage,
	edgeWeight float64,
	ctx *EvalContext,
) *ConsistencyReport {
	o.mu.Lock()
	o.evaluations++
	o.mu.Unlock()

	if ctx == nil {
		ctx = NewEvalContext()
	}

	report := NewConsistencyReport(msg.ID)
	activeChecks := o.activeChecks()

	// Avaliar cada check individualmente
	for _, checkName := range AllChecks {
		// Verificar se o check está ativo
		if !o.isCheckActive(checkName, activeChecks) {
			continue
		}

		result := o.evaluateCheck(checkName, msg, ctx)
		report.Checks[checkName] = result

		// Atualizar score mínimo (bottleneck)
		if result.Score < report.Score {
			report.Score = result.Score
		}

		// Verificar threshold
		threshold := o.thresholds.Get(checkName)
		if result.Score < threshold {
			report.Pruned = true
			if report.PruneReason == "" {
				report.PruneReason = fmt.Sprintf(
					"%s=%.3f < threshold=%.3f",
					checkName, result.Score, threshold,
				)
			}
			if result.Score <= ScoreBottom {
				report.ParadoxDetected = true
				report.PruneReason = fmt.Sprintf(
					"PARADOXO: %s", report.PruneReason,
				)
				break
			}
		}
	}

	// Score composto
	report.Score = o.compositeScore(report, activeChecks)

	// Ajustar peso
	if report.Pruned {
		report.AdjustedWeight = math.Inf(1)
		o.mu.Lock()
		o.pruned++
		o.mu.Unlock()
	} else {
		o.mu.Lock()
		o.accepted++
		o.mu.Unlock()
		report.AdjustedWeight = o.effectiveWeight(edgeWeight, report.Score)
	}

	return report
}

// evaluateCheck avalia um check individual.
func (o *ConsistencyOracle) evaluateCheck(
	name CheckName,
	msg *arkhecore.TemporalMessage,
	ctx *EvalContext,
) *CheckResult {
	switch name {
	case CheckHarmless:
		return o.checkHarmless(msg, ctx)
	case CheckParadoxFree:
		return o.checkParadoxFree(msg, ctx)
	case CheckEntropySafe:
		return o.checkEntropySafe(msg)
	case CheckCoherent:
		return o.checkCoherent(msg)
	case CheckZKValid:
		return o.checkZKValid(msg)
	case CheckQuantumTime:
		return o.checkQuantumTime(msg, ctx)
	case CheckSolarCoherence:
		return o.checkSolarCoherence(msg, ctx)
	case CheckGalacticAuth:
		return o.checkGalacticCoherence(msg)
	default:
		return NewCheckResult(name, ScoreTop)
	}
}

// ============================================================================
// CHECK 1: Harmless — a rota causa dano?
// ============================================================================

func (o *ConsistencyOracle) checkHarmless(
	msg *arkhecore.TemporalMessage,
	ctx *EvalContext,
) *CheckResult {
	violations := []string{}
	score := ScoreTop

	// Detectar loops
	if ctx.VisitedContains(msg.Sender) || ctx.VisitedContains(msg.Receiver) {
		violations = append(violations,
			fmt.Sprintf("LOOP: nó %s já visitado", msg.Receiver))
		score = ScoreBottom
	}

	// Verificar custo absurdo
	if ctx.AccumulatedCost > 1000 {
		violations = append(violations,
			fmt.Sprintf("Custo acumulado excessivo: %.2f", ctx.AccumulatedCost))
		score = min(score, 0.1)
	}

	return NewCheckResult(CheckHarmless, score, violations...)
}

// ============================================================================
// CHECK 2: Paradox-Free — a rota cria paradoxo temporal?
// ============================================================================

func (o *ConsistencyOracle) checkParadoxFree(
	msg *arkhecore.TemporalMessage,
	ctx *EvalContext,
) *CheckResult {
	violations := []string{}
	score := ScoreTop

	// Verificar consistência temporal
	if float64(msg.SourceTimestamp) > float64(msg.TargetTimestamp) {
		violations = append(violations,
			fmt.Sprintf("Paradoxo temporal: source_ts(%d) > target_ts(%d)",
				msg.SourceTimestamp, msg.TargetTimestamp))
		score = 0.05
	}

	// Verificar se destino "já aconteceu" no caminho
	if ctx.TemporalIndex > 0 {
		// Heurística: se o target timestamp é muito anterior ao contexto atual
		if msg.TargetTimestamp < arkhecore.Timestamp(int64(ctx.TemporalIndex)*int64(arkhecore.BlockInterval)) {
			violations = append(violations,
				fmt.Sprintf("Possível paradoxo: target=%d muito no passado (ctx=%d)",
					msg.TargetTimestamp, ctx.TemporalIndex))
			score = min(score, 0.2)
		}
	}

	return NewCheckResult(CheckParadoxFree, score, violations...)
}

// ============================================================================
// CHECK 3: Entropy-Safe — o custo informacional é aceitável?
// ============================================================================

func (o *ConsistencyOracle) checkEntropySafe(msg *arkhecore.TemporalMessage) *CheckResult {
	violations := []string{}
	score := ScoreTop

	// Estimar entropia baseada no tamanho do conteúdo
	contentLen := float64(len(msg.Content))
	payloadLen := float64(len(msg.Payload))

	// Conteúdo vazio é suspeito
	if contentLen < 1 && payloadLen < 1 {
		score = 0.5
	}

	// Payload excessivo pode indicar entropia
	if payloadLen > 1024*1024 { // 1MB
		violations = append(violations,
			fmt.Sprintf("Payload excessivo: %.0f bytes", payloadLen))
		score = Score(max(0, 1.0-(payloadLen/1024/1024/10)))
	}

	return NewCheckResult(CheckEntropySafe, score, violations...)
}

// ============================================================================
// CHECK 4: Coherent — a rota é temporalmente coerente?
// ============================================================================

func (o *ConsistencyOracle) checkCoherent(msg *arkhecore.TemporalMessage) *CheckResult {
	violations := []string{}
	score := ScoreTop

	// Freshness: verificar se a mensagem não expirou
	now := arkhecore.Now()
	msgAge := now - msg.SourceTimestamp

	if msgAge > 0 && float64(msgAge) > float64(arkhecore.BlockInterval*100) {
		// Mensagem mais velha que 10 blocos
		violations = append(violations,
			fmt.Sprintf("Mensagem desatualizada: age=%dms", msgAge/1e6))
		score = Score(max(0, 0.5-float64(msgAge)/float64(arkhecore.BlockInterval*1000)))
	}

	return NewCheckResult(CheckCoherent, score, violations...)
}

// ============================================================================
// CHECK 5: ZK Valid — há prova de conhecimento zero?
// ============================================================================

func (o *ConsistencyOracle) checkZKValid(msg *arkhecore.TemporalMessage) *CheckResult {
	violations := []string{}
	score := ScoreTop

	// Verificar se há prova ZK
	if len(msg.ZKProof) == 0 {
		// Sem prova ZK — penalidade leve
		score = 0.8
		// Não é violação, apenas menos confiável
	}

	// Em produção: verificar a prova ZK real
	// if msg.ZKProof != nil {
	//     valid := zk.Verify(msg.ZKProof, msg.Hash())
	//     if !valid {
	//         violations = append(violations, "ZK proof inválida")
	//         score = 0.3
	//     }
	// }

	return NewCheckResult(CheckZKValid, score, violations...)
}

// ============================================================================
// CHECK 6: Quantum-Time — consistência quântica temporal
// ============================================================================

func (o *ConsistencyOracle) checkQuantumTime(
	msg *arkhecore.TemporalMessage,
	ctx *EvalContext,
) *CheckResult {
	violations := []string{}
	score := ScoreTop

	// Verificar se há sobreposição temporal paradoxal
	// (simulação: verificar se timestamps são coerentes)
	if msg.SourceTimestamp > msg.TargetTimestamp {
		violations = append(violations,
			"Retrocausalidade não autorizada")
		score = 0.1
	}

	// Verificar "janela quântica" — tolerância de 100ms
	tolerance := arkhecore.Timestamp(100 * 1_000_000) // 100ms em nanossegundos
	if msg.TargetTimestamp-msg.SourceTimestamp > tolerance*1000 {
		// Grande gap temporal — verificar se justificado
		score = max(0.5, score-0.3)
	}

	return NewCheckResult(CheckQuantumTime, score, violations...)
}

// ============================================================================
// CHECK 7: Solar Coherence — coerência com o Sol
// ============================================================================

// SolarCoherenceChecker é a interface para dados solares em tempo real.
type SolarCoherenceChecker interface {
	IsSwitchbackActive() bool
	GetSwitchbackSeverity() float64
	GetSolarWindVelocity() float64
	GetAffectedRegion() string
}

func (o *ConsistencyOracle) checkSolarCoherence(
	msg *arkhecore.TemporalMessage,
	ctx *EvalContext,
) *CheckResult {
	violations := []string{}
	score := ScoreTop

	if o.solarModel == nil {
		// Sem modelo solar — usar score padrão
		return NewCheckResult(CheckSolarCoherence, ScoreTop)
	}

	// Verificar switchback ativo
	if o.solarModel.IsSwitchbackActive() {
		severity := Score(o.solarModel.GetSwitchbackSeverity())
		score = max(0, ScoreTop-severity*0.8)

		if score < o.thresholds.Get(CheckSolarCoherence) {
			violations = append(violations, fmt.Sprintf(
				"Switchback solar ativo: severidade=%.3f, região=%s",
				severity, o.solarModel.GetAffectedRegion()))
		}
	}

	return NewCheckResult(CheckSolarCoherence, score, violations...)
}

// ============================================================================
// CHECK 8: Galactic Coherence — coerência com o Ledger Galáctico
// ============================================================================

func (o *ConsistencyOracle) checkGalacticCoherence(
	msg *arkhecore.TemporalMessage,
) *CheckResult {
	violations := []string{}
	score := ScoreTop

	// Em produção: verificar contra ledger galáctico
	// Verificar se o nó (sender/receiver) está registrado
	// if !galacticLedger.IsRegistered(msg.Sender) {
	//     violations = append(violations, fmt.Sprintf("Nó %s não registrado no Ledger Galáctico", msg.Sender))
	//     score = 0.6
	// }

	return NewCheckResult(CheckGalacticAuth, score, violations...)
}

// ============================================================================
// Cálculo do Score Composto (Álgebra de Heyting)
// ============================================================================

// compositeScore calcula o score composto usando lógica de Heyting.
// É aqui que a estrutura algébrica se manifesta:
//   - meet (∧) = mínimo dos scores (bottleneck)
//   - join (∨) = média ponderada
//   - O resultado reflete a "verdade" intuicionista da consistência.
func (o *ConsistencyOracle) compositeScore(
	report *ConsistencyReport,
	activeChecks []CheckName,
) Score {
	if len(activeChecks) == 0 {
		return ScoreTop
	}

	// Calcular bottleneck (meet) e média ponderada (join ponderada)
	minScore := ScoreTop
	var weightedSum float64
	var totalWeight float64

	for _, name := range activeChecks {
		result, ok := report.Checks[name]
		if !ok {
			continue
		}

		weight := o.weights.Get(name)

		// Meet: track do mínimo (bottleneck)
		if result.Score < minScore {
			minScore = result.Score
		}

		// Weighted sum para a média
		weightedSum += float64(result.Score) * weight
		totalWeight += weight
	}

	if totalWeight == 0 {
		return ScoreBottom
	}

	avgScore := Score(weightedSum / totalWeight)

	if o.strictMode {
		// Strict: pure bottleneck (meet only)
		return minScore
	}

	// Flex: 70% média (join ponderada), 30% bottleneck (meet)
	// Isso implementa o operador intuicionista de forma balanceada
	return Score(0.7*float64(avgScore) + 0.3*float64(minScore))
}

// effectiveWeight calcula o peso ajustado pelo score de consistência.
func (o *ConsistencyOracle) effectiveWeight(rawWeight float64, score Score) float64 {
	// Score=1.0 → fator=1.0 (rota perfeita)
	// Score=0.5 → fator=2.0 (rota questionável)
	// Score=0.1 → fator=10.0 (rota evitada)
	if score <= 0 {
		return math.Inf(1)
	}
	return rawWeight / float64(max(score, 0.01))
}

// ============================================================================
// Auxiliares
// ============================================================================

func (o *ConsistencyOracle) activeChecks() []CheckName {
	// Retorna todos as checks que não são opcionais ou que estão habilitadas
	result := make([]CheckName, 0, len(AllChecks))
	for _, c := range AllChecks {
		// Solar e Galactic podem ser desabilitados
		if c == CheckSolarCoherence || c == CheckGalacticAuth {
			result = append(result, c) // Simplificado: sempre ativos
		} else {
			result = append(result, c)
		}
	}
	return result
}

func (o *ConsistencyOracle) isCheckActive(name CheckName, active []CheckName) bool {
	for _, c := range active {
		if c == name {
			return true
		}
	}
	return false
}

// ============================================================================
// Propriedades Estatísticas
// ============================================================================

// OracleStats contém estatísticas de uso do Oracle.
type OracleStats struct {
	Evaluations  uint64            `json:"evaluations"`
	Pruned       uint64            `json:"pruned"`
	Accepted     uint64            `json:"accepted"`
	PruningRate  float64           `json:"pruning_rate"`
	Thresholds   map[string]Score  `json:"thresholds"`
	ActiveChecks []CheckName       `json:"active_checks"`
}

// Stats retorna estatísticas do Oracle.
func (o *ConsistencyOracle) Stats() *OracleStats {
	o.mu.RLock()
	defer o.mu.RUnlock()

	total := o.evaluations
	stats := &OracleStats{
		Evaluations: total,
		Pruned:      o.pruned,
		Accepted:    o.accepted,
	}

	if total > 0 {
		stats.PruningRate = float64(o.pruned) / float64(total)
	}

	stats.ActiveChecks = AllChecks

	return stats
}

// ============================================================================
// OPERAÇÕES DE ÁLGEBRA DE HEYTING
// ============================================================================

// Meet (∧): intersecção — o pior score entre p e q.
func HeytingMeet(p, q Score) Score {
	return min(p, q)
}

// Join (∨): união — o melhor score entre p e q.
func HeytingJoin(p, q Score) Score {
	return max(p, q)
}

// Implication (→): a operação mais importante da álgebra de Heyting.
// p → q = "se p então q" — definida como o maior r tal que p ∧ r ≤ q.
// Na prática: implication(a, b) = (a ≤ b) ? 1.0 : b
func HeytingImplication(p, q Score) Score {
	if p <= q {
		return ScoreTop
	}
	return q
}

// Negation (¬): pseudocomplemento — ¬p = p → ⊥
func HeytingNegation(p Score) Score {
	return HeytingImplication(p, ScoreBottom)
}

// BiImplication (↔): equivalência intuicionista.
func HeytingBiImplication(p, q Score) Score {
	return min(HeytingImplication(p, q), HeytingImplication(q, p))
}
