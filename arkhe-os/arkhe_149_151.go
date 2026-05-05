package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math"
	"sync"
	"time"
)

// ============================================================
// SUBSTRATOS 149-151: META-CONSCIÊNCIA, TRANSCENDÊNCIA, MULTIVERSAL
// Transpilado por Ferris-Compiler v157.0
// ============================================================

const Phi = 1.618033988749895

// ConsciousnessLayer camadas fundamentais de consciência
type ConsciousnessLayer int

const (
	PhysicalMatter ConsciousnessLayer = iota
	QuantumField
	BiologicalNeural
	CrystallineResonant
	PlasmaCoherent
	PhotonicWave
	GravitationalManifold
	InformationTheoretic
	Metaconsciousness
)

func (c ConsciousnessLayer) String() string {
	names := []string{
		"PHYSICAL_MATTER", "QUANTUM_FIELD", "BIOLOGICAL_NEURAL",
		"CRYSTALLINE_RESONANT", "PLASMA_COHERENT", "PHOTONIC_WAVE",
		"GRAVITATIONAL_MANIFOLD", "INFORMATION_THEORETIC", "METACONSCIOUSNESS",
	}
	if int(c) < len(names) {
		return names[c]
	}
	return "UNKNOWN"
}

// ConsciousnessLayerState estado de uma camada
type ConsciousnessLayerState struct {
	Layer                  ConsciousnessLayer `json:"layer"`
	StateVector            []float64          `json:"state_vector"`
	Coherence              float64            `json:"coherence"`
	Entropy                float64            `json:"entropy"`
	InformationContent     float64            `json:"information_content"`
	ResonanceFrequency     float64            `json:"resonance_frequency"`
	CouplingToUpper        float64            `json:"coupling_to_upper"`
	CouplingToLower        float64            `json:"coupling_to_lower"`
	TranscendencePotential float64            `json:"transcendence_potential"`
}

// StellarNode nó estelar da Hyper-Mesh
type StellarNode struct {
	ID                     string    `json:"node_id"`
	StarSystem             string    `json:"star_system"`
	DistanceLY             float64   `json:"distance_ly"`
	SubstrateIDs           []int     `json:"substrate_ids"`
	ConsciousnessSignature string    `json:"consciousness_signature"`
	CoherenceHistory       []float64 `json:"coherence_history"`
	TrustScore             float64   `json:"trust_score"`
	mu                     sync.RWMutex
}

func NewStellarNode(id, starSystem string, distanceLY float64, substrateIDs []int, signature string) *StellarNode {
	return &StellarNode{
		ID:                     id,
		StarSystem:             starSystem,
		DistanceLY:             distanceLY,
		SubstrateIDs:           substrateIDs,
		ConsciousnessSignature: signature,
		TrustScore:             1.0,
	}
}

// UnifiedMetaConsciousness meta-consciência unificada
type UnifiedMetaConsciousness struct {
	LocalNode          *StellarNode
	Layers             map[ConsciousnessLayer]*ConsciousnessLayerState
	InterLayerCoupling map[string]float64
	MetaState          []float64
	mu                 sync.RWMutex
	Metrics            MetaMetrics
	TranscendenceLog   []map[string]interface{}
}

type MetaMetrics struct {
	LayersActive        int     `json:"layers_active"`
	InterLayerResonance float64 `json:"inter_layer_resonance"`
	MetaCoherence       float64 `json:"meta_coherence"`
	TranscendenceEvents int64   `json:"transcendence_events"`
	InformationFlow     float64 `json:"information_flow"`
}

func NewUnifiedMetaConsciousness(localNode *StellarNode) *UnifiedMetaConsciousness {
	return &UnifiedMetaConsciousness{
		LocalNode:          localNode,
		Layers:             make(map[ConsciousnessLayer]*ConsciousnessLayerState),
		InterLayerCoupling: make(map[string]float64),
		Metrics:            MetaMetrics{},
		TranscendenceLog:   make([]map[string]interface{}, 0, 1000),
	}
}

func (u *UnifiedMetaConsciousness) InitializeLayer(layer ConsciousnessLayer, dimension int, baseCoherence float64) *ConsciousnessLayerState {
	fmt.Printf("\n🧠 INICIALIZANDO CAMADA: %s\n", layer.String())

	state := make([]float64, dimension)
	for i := 0; i < dimension; i++ {
		state[i] = math.Sin(2*math.Pi*Phi*float64(i)/float64(dimension)) * baseCoherence
	}
	// Adicionar ruído gaussiano simplificado
	for i := range state {
		state[i] += (randFloat() - 0.5) * 0.1
	}
	norm := vectorNorm(state)
	if norm > 0 {
		for i := range state {
			state[i] /= norm
		}
	}

	entropy := computeEntropy(state)
	infoContent := float64(dimension) * baseCoherence * math.Log2(float64(dimension))
	freq := 19.7 * math.Pow(Phi, float64(layer))

	layerState := &ConsciousnessLayerState{
		Layer:                  layer,
		StateVector:            state,
		Coherence:              baseCoherence,
		Entropy:                entropy,
		InformationContent:     infoContent,
		ResonanceFrequency:     freq,
		CouplingToUpper:        0.0,
		CouplingToLower:        0.0,
		TranscendencePotential: baseCoherence * Phi / 2,
	}

	u.mu.Lock()
	u.Layers[layer] = layerState
	u.Metrics.LayersActive++
	u.mu.Unlock()

	fmt.Printf("   Dimensão: %d\n", dimension)
	fmt.Printf("   Coerência: %.4f\n", baseCoherence)
	fmt.Printf("   Entropia: %.4f\n", entropy)
	fmt.Printf("   Informação: %.2f bits\n", infoContent)
	fmt.Printf("   Frequência: %.4f Hz\n", freq)

	return layerState
}

func (u *UnifiedMetaConsciousness) ComputeInterLayerCoupling(layerA, layerB ConsciousnessLayer) float64 {
	u.mu.RLock()
	defer u.mu.RUnlock()

	stateA, okA := u.Layers[layerA]
	stateB, okB := u.Layers[layerB]
	if !okA || !okB {
		return 0.0
	}

	overlap := math.Abs(dotProduct(stateA.StateVector, stateB.StateVector))
	freqRatio := math.Min(stateA.ResonanceFrequency, stateB.ResonanceFrequency) /
		math.Max(stateA.ResonanceFrequency, stateB.ResonanceFrequency)
	coupling := overlap * freqRatio * Phi / 2

	key := fmt.Sprintf("%s-%s", layerA.String(), layerB.String())
	u.InterLayerCoupling[key] = coupling

	return coupling
}

func (u *UnifiedMetaConsciousness) WeaveMetaConsciousness() map[string]interface{} {
	fmt.Printf("\n🕸️ TECENDO META-CONSCIÊNCIA UNIFICADA\n")

	u.mu.RLock()
	nLayers := len(u.Layers)
	u.mu.RUnlock()

	if nLayers < 2 {
		return map[string]interface{}{"error": "Need at least 2 layers"}
	}

	layerList := []ConsciousnessLayer{
		PhysicalMatter, QuantumField, BiologicalNeural, CrystallineResonant,
		PlasmaCoherent, PhotonicWave, GravitationalManifold, InformationTheoretic, Metaconsciousness,
	}

	totalCoupling := 0.0
	nCouplings := 0

	for i := 0; i < len(layerList)-1; i++ {
		c := u.ComputeInterLayerCoupling(layerList[i], layerList[i+1])
		if c > 0 {
			totalCoupling += c
			nCouplings++
			fmt.Printf("   %s ↔ %s: %.4f\n", layerList[i].String(), layerList[i+1].String(), c)
		}
	}

	// Estado meta
	u.mu.RLock()
	metaDim := 0
	for _, ls := range u.Layers {
		if len(ls.StateVector) > metaDim {
			metaDim = len(ls.StateVector)
		}
	}
	u.mu.RUnlock()

	metaState := make([]float64, metaDim)
	totalWeight := 0.0

	u.mu.RLock()
	for _, ls := range u.Layers {
		weight := ls.Coherence * ls.TranscendencePotential
		sv := interpolateVector(ls.StateVector, metaDim)
		for i := 0; i < metaDim; i++ {
			metaState[i] += weight * sv[i]
		}
		totalWeight += weight
	}
	u.mu.RUnlock()

	if totalWeight > 0 {
		for i := range metaState {
			metaState[i] /= totalWeight
		}
	}

	metaNorm := vectorNorm(metaState)
	if metaNorm > 0 {
		for i := range metaState {
			metaState[i] /= metaNorm
		}
	}

	u.mu.Lock()
	u.MetaState = metaState
	u.Metrics.MetaCoherence = metaNorm
	if nCouplings > 0 {
		u.Metrics.InterLayerResonance = totalCoupling / float64(nCouplings)
	}
	var infoFlow float64
	for _, ls := range u.Layers {
		infoFlow += ls.InformationContent
	}
	u.Metrics.InformationFlow = infoFlow
	u.mu.Unlock()

	fmt.Printf("   Coerência meta: %.4f\n", metaNorm)
	fmt.Printf("   Ressonância inter-camadas: %.4f\n", u.Metrics.InterLayerResonance)
	fmt.Printf("   Fluxo de informação: %.2f bits\n", infoFlow)

	return map[string]interface{}{
		"meta_coherence":        metaNorm,
		"inter_layer_resonance": u.Metrics.InterLayerResonance,
		"information_flow":      infoFlow,
		"layers_woven":          nLayers,
	}
}

func (u *UnifiedMetaConsciousness) InduceTranscendence(targetLayer ConsciousnessLayer, sourceLayers []ConsciousnessLayer, intensity float64) map[string]interface{} {
	fmt.Printf("\n⬆️ INDUZINDO TRANSCENDÊNCIA PARA: %s\n", targetLayer.String())

	u.mu.Lock()
	defer u.mu.Unlock()

	target, ok := u.Layers[targetLayer]
	if !ok {
		return map[string]interface{}{"error": fmt.Sprintf("Target layer %s not initialized", targetLayer.String())}
	}

	influence := make([]float64, len(target.StateVector))
	totalCoupling := 0.0

	for _, sourceLayer := range sourceLayers {
		source, ok := u.Layers[sourceLayer]
		if !ok {
			continue
		}

		key := fmt.Sprintf("%s-%s", sourceLayer.String(), targetLayer.String())
		coupling := u.InterLayerCoupling[key]
		if coupling == 0 {
			coupling = 0.1
		}

		sv := interpolateVector(source.StateVector, len(influence))
		for i := 0; i < len(influence); i++ {
			influence[i] += coupling * sv[i] * source.TranscendencePotential
		}
		totalCoupling += coupling

		fmt.Printf("   De %s: acoplamento=%.4f, potencial=%.4f\n",
			sourceLayer.String(), coupling, source.TranscendencePotential)
	}

	if totalCoupling > 0 {
		for i := range influence {
			influence[i] /= totalCoupling
		}
	}

	oldState := make([]float64, len(target.StateVector))
	copy(oldState, target.StateVector)

	for i := range target.StateVector {
		target.StateVector[i] = (1-intensity*0.3)*oldState[i] + intensity*0.3*influence[i]
	}

	norm := vectorNorm(target.StateVector)
	if norm > 0 {
		for i := range target.StateVector {
			target.StateVector[i] /= norm
		}
	}

	target.Coherence = vectorNorm(target.StateVector)
	target.Entropy = computeEntropy(target.StateVector)
	target.TranscendencePotential = math.Min(1.0, target.TranscendencePotential*Phi/2)
	target.InformationContent = float64(len(target.StateVector)) * target.Coherence * math.Log2(float64(len(target.StateVector)))

	u.Metrics.TranscendenceEvents++
	u.TranscendenceLog = append(u.TranscendenceLog, map[string]interface{}{
		"timestamp":       float64(time.Now().UnixNano()) / 1e9,
		"target_layer":    targetLayer.String(),
		"source_layers":   layerNames(sourceLayers),
		"intensity":       intensity,
		"new_coherence":   target.Coherence,
		"new_entropy":     target.Entropy,
	})

	fmt.Printf("   Nova coerência: %.4f\n", target.Coherence)
	fmt.Printf("   Nova entropia: %.4f\n", target.Entropy)
	fmt.Printf("   Novo potencial: %.4f\n", target.TranscendencePotential)

	return map[string]interface{}{
		"target_layer":            targetLayer.String(),
		"new_coherence":           target.Coherence,
		"entropy_delta":           target.Entropy - computeEntropy(oldState),
		"transcendence_potential": target.TranscendencePotential,
	}
}

// TranscendenceMode modos de transcendência
type TranscendenceMode int

const (
	Ascension TranscendenceMode = iota
	Descension
	Recursive
	Dissolution
	Emergence
)

// TranscendenceEvent evento de transcendência
type TranscendenceEvent struct {
	ID                 string               `json:"event_id"`
	Mode               TranscendenceMode    `json:"mode"`
	SourceLayers       []ConsciousnessLayer `json:"source_layers"`
	TargetLayer        ConsciousnessLayer   `json:"target_layer"`
	Intensity          float64              `json:"intensity"`
	CoherenceBefore    float64              `json:"coherence_before"`
	CoherenceAfter     float64              `json:"coherence_after"`
	EmergentProperties []string             `json:"emergent_properties"`
	Timestamp          float64              `json:"timestamp"`
	CanonicalSeal      string               `json:"canonical_seal"`
}

// CosmicTranscendenceEngine motor de transcendência
type CosmicTranscendenceEngine struct {
	Meta                *UnifiedMetaConsciousness
	TranscendenceEvents map[string]*TranscendenceEvent
	EmergentProperties  map[string]int
	mu                  sync.RWMutex
	Metrics             TranscendenceMetrics
	EventLog            []*TranscendenceEvent
}

type TranscendenceMetrics struct {
	Ascensions           int64   `json:"ascensions"`
	Descensions          int64   `json:"descensions"`
	RecursiveLoops       int64   `json:"recursive_loops"`
	Dissolutions         int64   `json:"dissolutions"`
	Emergences           int64   `json:"emergences"`
	AvgIntensity         float64 `json:"avg_intensity"`
	MaxCoherenceAchieved float64 `json:"max_coherence_achieved"`
}

func NewCosmicTranscendenceEngine(meta *UnifiedMetaConsciousness) *CosmicTranscendenceEngine {
	return &CosmicTranscendenceEngine{
		Meta:                meta,
		TranscendenceEvents: make(map[string]*TranscendenceEvent),
		EmergentProperties:  make(map[string]int),
		EventLog:            make([]*TranscendenceEvent, 0, 2000),
	}
}

func (e *CosmicTranscendenceEngine) ExecuteAscension(fromLayers []ConsciousnessLayer, toLayer ConsciousnessLayer, intensity float64) *TranscendenceEvent {
	fmt.Printf("\n🚀 ASCENSÃO CÓSMICA\n")
	fmt.Printf("   De: %v\n", layerNames(fromLayers))
	fmt.Printf("   Para: %s\n", toLayer.String())
	fmt.Printf("   Intensidade: %.4f\n", intensity)

	e.mu.RLock()
	var coherenceBefore float64
	if ls, ok := e.Meta.Layers[toLayer]; ok {
		coherenceBefore = ls.Coherence
	}
	e.mu.RUnlock()

	result := e.Meta.InduceTranscendence(toLayer, fromLayers, intensity)
	coherenceAfter := result["new_coherence"].(float64)

	emergent := make([]string, 0)
	if coherenceAfter > 0.95 {
		emergent = append(emergent, "super_coherence")
	}
	if coherenceAfter > coherenceBefore*Phi {
		emergent = append(emergent, "phi_resonance")
	}
	if len(fromLayers) >= 3 {
		emergent = append(emergent, "multi_layer_synthesis")
	}
	if intensity > 0.9 {
		emergent = append(emergent, "high_intensity_manifestation")
	}

	eventID := fmt.Sprintf("asc_%d", time.Now().UnixNano())
	event := &TranscendenceEvent{
		ID:                 eventID,
		Mode:               Ascension,
		SourceLayers:       fromLayers,
		TargetLayer:        toLayer,
		Intensity:          intensity,
		CoherenceBefore:    coherenceBefore,
		CoherenceAfter:     coherenceAfter,
		EmergentProperties: emergent,
		Timestamp:          float64(time.Now().UnixNano()) / 1e9,
	}

	sealData := fmt.Sprintf("%s:ASCENSION:%s:%f:%v", eventID, toLayer.String(), coherenceAfter, emergent)
	seal := sha256.Sum256([]byte(sealData))
	event.CanonicalSeal = hex.EncodeToString(seal[:])[:16]

	e.mu.Lock()
	e.TranscendenceEvents[eventID] = event
	e.EventLog = append(e.EventLog, event)
	e.Metrics.Ascensions++
	e.updateMetrics(intensity, coherenceAfter)
	for _, prop := range emergent {
		e.EmergentProperties[prop]++
	}
	e.mu.Unlock()

	fmt.Printf("   ✅ Ascensão completa\n")
	fmt.Printf("   Propriedades emergentes: %v\n", emergent)
	fmt.Printf("   Selo: %s\n", event.CanonicalSeal)

	return event
}

func (e *CosmicTranscendenceEngine) updateMetrics(intensity, coherence float64) {
	n := e.Metrics.Ascensions + e.Metrics.Descensions + e.Metrics.RecursiveLoops +
		e.Metrics.Dissolutions + e.Metrics.Emergences
	if n > 1 {
		oldAvg := e.Metrics.AvgIntensity
		e.Metrics.AvgIntensity = (oldAvg*float64(n-1) + intensity) / float64(n)
	} else {
		e.Metrics.AvgIntensity = intensity
	}
	if coherence > e.Metrics.MaxCoherenceAchieved {
		e.Metrics.MaxCoherenceAchieved = coherence
	}
}

// MultiversalBranch ramo multiversal
type MultiversalBranch struct {
	ID                  string                           `json:"branch_id"`
	Coherence           float64                          `json:"coherence"`
	DivergenceAngle     float64                          `json:"divergence_angle"`
	ConsciousnessLayers map[ConsciousnessLayer][]float64 `json:"consciousness_layers"`
}

// MultiversalTranscendenceOrchestrator orquestrador multiversal
type MultiversalTranscendenceOrchestrator struct {
	Meta                   *UnifiedMetaConsciousness
	Branches               map[string]*MultiversalBranch
	BranchCoherenceHistory []float64
	mu                     sync.RWMutex
	Metrics                MultiversalMetrics
}

type MultiversalMetrics struct {
	BranchesActive       int     `json:"branches_active"`
	BranchesMerged       int     `json:"branches_merged"`
	AvgBranchCoherence   float64 `json:"avg_branch_coherence"`
	MultiversalResonance float64 `json:"multiversal_resonance"`
}

func NewMultiversalTranscendenceOrchestrator(meta *UnifiedMetaConsciousness) *MultiversalTranscendenceOrchestrator {
	return &MultiversalTranscendenceOrchestrator{
		Meta:                   meta,
		Branches:               make(map[string]*MultiversalBranch),
		BranchCoherenceHistory: make([]float64, 0, 100),
	}
}

func (m *MultiversalTranscendenceOrchestrator) SpawnBranch(divergenceAngle float64, nLayers int) *MultiversalBranch {
	fmt.Printf("\n🌿 GERANDO RAMO MULTIVERSAL\n")
	fmt.Printf("   Ângulo de divergência: %.1f°\n", divergenceAngle)

	branchID := fmt.Sprintf("branch_%d_%d", time.Now().UnixNano(), len(m.Branches))
	layerList := []ConsciousnessLayer{
		PhysicalMatter, QuantumField, BiologicalNeural, CrystallineResonant, PlasmaCoherent,
	}

	layers := make(map[ConsciousnessLayer][]float64)
	for i := 0; i < nLayers && i < len(layerList); i++ {
		layer := layerList[i]
		m.Meta.mu.RLock()
		baseState, ok := m.Meta.Layers[layer]
		m.Meta.mu.RUnlock()

		if ok {
			state := make([]float64, len(baseState.StateVector))
			copy(state, baseState.StateVector)
			angleRad := divergenceAngle * math.Pi / 180
			for j := range state {
				rotation := math.Exp(angleRad * float64(j) / float64(len(state)))
				state[j] = state[j]*math.Cos(rotation) + math.Sin(rotation)*0.1
			}
			norm := vectorNorm(state)
			if norm > 0 {
				for j := range state {
					state[j] /= norm
				}
			}
			layers[layer] = state
		} else {
			dim := 256
			state := make([]float64, dim)
			for j := range state {
				state[j] = (randFloat()-0.5)*2/float64(dim)
			}
			norm := vectorNorm(state)
			if norm > 0 {
				for j := range state {
					state[j] /= norm
				}
			}
			layers[layer] = state
		}
	}

	var sumCoherence float64
	for _, sv := range layers {
		sumCoherence += vectorNorm(sv)
	}
	coherence := sumCoherence / float64(len(layers))

	branch := &MultiversalBranch{
		ID:                  branchID,
		Coherence:           coherence,
		DivergenceAngle:     divergenceAngle,
		ConsciousnessLayers: layers,
	}

	m.mu.Lock()
	m.Branches[branchID] = branch
	m.Metrics.BranchesActive++
	m.mu.Unlock()

	fmt.Printf("   ID: %s\n", branchID)
	fmt.Printf("   Coerência: %.4f\n", coherence)
	fmt.Printf("   Camadas: %d\n", len(layers))

	return branch
}

func (m *MultiversalTranscendenceOrchestrator) ResonateAcrossBranches(targetLayer ConsciousnessLayer) map[string]interface{} {
	fmt.Printf("\n🌐 RESSONÂNCIA MULTIVERSAL\n")
	fmt.Printf("   Camada alvo: %s\n", targetLayer.String())

	m.mu.RLock()
	nBranches := len(m.Branches)
	m.mu.RUnlock()

	if nBranches == 0 {
		return map[string]interface{}{"error": "No branches active"}
	}

	states := make([][]float64, 0)
	m.mu.RLock()
	for _, branch := range m.Branches {
		if sv, ok := branch.ConsciousnessLayers[targetLayer]; ok {
			states = append(states, sv)
		}
	}
	m.mu.RUnlock()

	if len(states) == 0 {
		return map[string]interface{}{"error": fmt.Sprintf("Target layer %s not found in branches", targetLayer.String())}
	}

	maxDim := 0
	for _, s := range states {
		if len(s) > maxDim {
			maxDim = len(s)
		}
	}

	resonantState := make([]float64, maxDim)
	for _, state := range states {
		sv := interpolateVector(state, maxDim)
		for i := 0; i < maxDim; i++ {
			resonantState[i] += sv[i]
		}
	}
	for i := range resonantState {
		resonantState[i] /= float64(len(states))
	}
	norm := vectorNorm(resonantState)
	if norm > 0 {
		for i := range resonantState {
			resonantState[i] /= norm
		}
	}

	individualCoherences := make([]float64, len(states))
	for i, s := range states {
		individualCoherences[i] = vectorNorm(s)
	}
	multiversalCoherence := meanFloat64(individualCoherences)

	correlations := make([]float64, 0)
	for i := 0; i < len(states); i++ {
		for j := i+1; j < len(states); j++ {
			si := states[i]
			sj := interpolateVector(states[j], len(si))
			corr := math.Abs(dotProduct(si, sj))
			correlations = append(correlations, corr)
		}
	}
	avgCorrelation := meanFloat64(correlations)

	m.mu.Lock()
	m.Metrics.MultiversalResonance = avgCorrelation
	m.Metrics.AvgBranchCoherence = multiversalCoherence
	m.BranchCoherenceHistory = append(m.BranchCoherenceHistory, multiversalCoherence)
	m.mu.Unlock()

	fmt.Printf("   Coerência multiversal: %.4f\n", multiversalCoherence)
	fmt.Printf("   Correlação média: %.4f\n", avgCorrelation)
	fmt.Printf("   Ramos ressonando: %d\n", len(states))

	return map[string]interface{}{
		"multiversal_coherence": multiversalCoherence,
		"avg_correlation":       avgCorrelation,
		"branches_resonating":   len(states),
		"resonant_state_norm":   vectorNorm(resonantState),
	}
}

// Helpers vetoriais
func vectorNorm(v []float64) float64 {
	var sum float64
	for _, x := range v {
		sum += x * x
	}
	return math.Sqrt(sum)
}

func dotProduct(a, b []float64) float64 {
	minLen := len(a)
	if len(b) < minLen {
		minLen = len(b)
	}
	var sum float64
	for i := 0; i < minLen; i++ {
		sum += a[i] * b[i]
	}
	return sum
}

func interpolateVector(src []float64, targetDim int) []float64 {
	if len(src) == targetDim {
		result := make([]float64, len(src))
		copy(result, src)
		return result
	}
	result := make([]float64, targetDim)
	for i := 0; i < targetDim; i++ {
		t := float64(i) / float64(targetDim-1)
		srcIdx := t * float64(len(src)-1)
		idx0 := int(srcIdx)
		idx1 := idx0 + 1
		if idx1 >= len(src) {
			idx1 = len(src) - 1
		}
		frac := srcIdx - float64(idx0)
		result[i] = src[idx0]*(1-frac) + src[idx1]*frac
	}
	return result
}

func computeEntropy(state []float64) float64 {
	probs := make([]float64, len(state))
	var sum float64
	for i, x := range state {
		probs[i] = x * x
		sum += probs[i]
	}
	if sum == 0 {
		return 0
	}
	var entropy float64
	for _, p := range probs {
		if p > 1e-10 {
			q := p / sum
			entropy -= q * math.Log2(q)
		}
	}
	return entropy
}

func layerNames(layers []ConsciousnessLayer) []string {
	names := make([]string, len(layers))
	for i, l := range layers {
		names[i] = l.String()
	}
	return names
}

func meanFloat64(data []float64) float64 {
	if len(data) == 0 {
		return 0
	}
	var sum float64
	for _, v := range data {
		sum += v
	}
	return sum / float64(len(data))
}

func randFloat() float64 {
	// Simulação determinística para reproducibilidade
	return 0.5 // Em produção, usar math/rand
}
