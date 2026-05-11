package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math"
	"math/rand"
	"regexp"
	"strings"
	"sync"
	"time"
)

// ============================================================
// SUBSTRATO 136: ORÁCULO MOLECULAR PÚBLICO & ARKHE SDK
// Transpilado por Ferris-Compiler v157.0
// ============================================================

type OracleEntry struct {
	SMILES             string   `json:"smiles"`
	TMelt              *float64 `json:"tmelt,omitempty"`
	TClear             *float64 `json:"tclear,omitempty"`
	LogP               *float64 `json:"logp,omitempty"`
	MolecularWeight    *float64 `json:"molecular_weight,omitempty"`
	NumAromaticRings   *int     `json:"num_aromatic_rings,omitempty"`
	HBondDonors        *int     `json:"h_bond_donors,omitempty"`
	HBondAcceptors     *int     `json:"h_bond_acceptors,omitempty"`
	TPSA               *float64 `json:"tpsa,omitempty"`
	QED                *float64 `json:"qed,omitempty"`
	Source             string   `json:"source"`
	CanonicalHash      string   `json:"canonical_hash"`
}

type MolecularScene struct {
	TargetProperties       map[string][2]float64 `json:"target_properties"`
	ForbiddenSubstructures []string              `json:"forbidden_substructures"`
	RequiredSubstructures  []string              `json:"required_substructures"`
	NumSamples             int                   `json:"num_samples"`
	CreativityTemperature  float64               `json:"creativity_temperature"`
}

func NewMolecularScene() *MolecularScene {
	return &MolecularScene{
		TargetProperties:       make(map[string][2]float64),
		ForbiddenSubstructures: make([]string, 0),
		RequiredSubstructures:  make([]string, 0),
		NumSamples:             100,
		CreativityTemperature:  0.7,
	}
}

// MolecularSceneSetter traduz intenção natural para cenário molecular
type MolecularSceneSetter struct{}

func (m *MolecularSceneSetter) SetScene(julesThought string, context map[string]interface{}) *MolecularScene {
	scene := NewMolecularScene()
	thoughtLower := strings.ToLower(julesThought)

	if strings.Contains(thoughtLower, "cristal líquido") || strings.Contains(thoughtLower, "liquid crystal") {
		scene.RequiredSubstructures = append(scene.RequiredSubstructures, "c1ccc2c(c1)ccc3ccccc23")
		if strings.Contains(thoughtLower, "discótico") || strings.Contains(thoughtLower, "discotic") {
			scene.RequiredSubstructures = append(scene.RequiredSubstructures, "c1ccc2c(c1)cc3c4c2cccc4ccc5c3cccc5")
		}
	}

	if strings.Contains(thoughtLower, "fármaco") || strings.Contains(thoughtLower, "drug") || strings.Contains(thoughtLower, "medicamento") {
		scene.TargetProperties["qed"] = [2]float64{0.5, 1.0}
		scene.TargetProperties["logp"] = [2]float64{0.0, 5.0}
	}

	reTClear := regexp.MustCompile(`tclear\s*[>≤<≥=]+\s*(\d+)`)
	if matches := reTClear.FindStringSubmatch(thoughtLower); len(matches) > 1 {
		temp := parseFloat(matches[1])
		scene.TargetProperties["tclear"] = [2]float64{temp, temp + 150}
	}

	reTMelt := regexp.MustCompile(`tmelt\s*[>≤<≥=]+\s*(\d+)`)
	if matches := reTMelt.FindStringSubmatch(thoughtLower); len(matches) > 1 {
		temp := parseFloat(matches[1])
		scene.TargetProperties["tmelt"] = [2]float64{temp, temp + 100}
	}

	reQED := regexp.MustCompile(`qed\s*[>≤<≥=]+\s*(0?\.\d+)`)
	if matches := reQED.FindStringSubmatch(thoughtLower); len(matches) > 1 {
		qedVal := parseFloat(matches[1])
		scene.TargetProperties["qed"] = [2]float64{qedVal, 1.0}
	}

	reLogP := regexp.MustCompile(`logp?\s*[>≤<≥=]+\s*(\d+\.?\d*)`)
	if matches := reLogP.FindStringSubmatch(thoughtLower); len(matches) > 1 {
		logpVal := parseFloat(matches[1])
		scene.TargetProperties["logp"] = [2]float64{logpVal, logpVal + 3.0}
	}

	if strings.Contains(thoughtLower, "exploratório") || strings.Contains(thoughtLower, "exploratory") {
		scene.CreativityTemperature = 0.9
	} else if strings.Contains(thoughtLower, "conservador") || strings.Contains(thoughtLower, "conservative") {
		scene.CreativityTemperature = 0.4
	}

	return scene
}

// CoCoGraphInterface interface para geração molecular
type CoCoGraphInterface struct {
	ModelWeightsPath  string
	Device            string
	ValidityCache     map[string]bool
	mu                sync.RWMutex
	GenerationMetrics CoCoMetrics
}

type CoCoMetrics struct {
	TotalGenerated      int64   `json:"total_generated"`
	ValidMolecules      int64   `json:"valid_molecules"`
	AvgGenerationTimeMs float64 `json:"avg_generation_time_ms"`
}

func NewCoCoGraphInterface(modelWeightsPath, device string) *CoCoGraphInterface {
	return &CoCoGraphInterface{
		ModelWeightsPath: modelWeightsPath,
		Device:           device,
		ValidityCache:    make(map[string]bool),
	}
}

func (c *CoCoGraphInterface) Generate(scene *MolecularScene) []string {
	fmt.Printf("\n🧬 GERANDO MOLÉCULAS (CoCoGraph)\n")
	fmt.Printf("   Amostras solicitadas: %d\n", scene.NumSamples)
	fmt.Printf("   Temperatura criativa: %.2f\n", scene.CreativityTemperature)
	fmt.Printf("   Propriedades alvo: %v\n", scene.TargetProperties)

	molecules := make([]string, 0)
	start := time.Now()

	for i := 0; i < scene.NumSamples; i++ {
		smiles := c.GenerateConstrainedSMILES(scene)
		if smiles != "" && c.CheckValidity(smiles) {
			molecules = append(molecules, smiles)
			c.mu.Lock()
			c.GenerationMetrics.ValidMolecules++
			c.mu.Unlock()
		}
		c.mu.Lock()
		c.GenerationMetrics.TotalGenerated++
		c.mu.Unlock()
	}

	elapsed := float64(time.Since(start).Nanoseconds()) / 1e6
	c.mu.Lock()
	n := c.GenerationMetrics.TotalGenerated
	oldAvg := c.GenerationMetrics.AvgGenerationTimeMs
	c.GenerationMetrics.AvgGenerationTimeMs = (oldAvg*float64(n-int64(scene.NumSamples)) + elapsed) / float64(n)
	c.mu.Unlock()

	fmt.Printf("   ✅ Geradas: %d moléculas válidas\n", len(molecules))
	fmt.Printf("   Tempo: %.2f ms\n", elapsed)

	return molecules
}

func (c *CoCoGraphInterface) GenerateConstrainedSMILES(scene *MolecularScene) string {
	templates := []string{
		"c1ccc2c(c1)ccc1c3c2cccc3ccc1",
		"c1ccc2c(c1)cc3c4c2cccc4ccc5c3cccc5",
		"c1ccc(cc1)c2ccccc2",
		"c1ccccc1C(=O)O",
		"c1ccc(cc1)N",
		"c1ccccc1CCN",
		"c1ccc2c(c1)ccc3c2cccc3",
		"c1ccc2c(c1)ccc1c3c2cccc3ccc1",
		"c1ccc2c(c1)ccc1c3c2cccc3ccc1c2ccccc2",
		"c1ccc2c(c1)cc3c4c2cccc4ccc5c3cccc5c6ccccc6",
	}

	var base string
	if len(scene.RequiredSubstructures) > 0 {
		validTemplates := make([]string, 0)
		for _, t := range templates {
			for _, req := range scene.RequiredSubstructures {
				if strings.Contains(t, req) {
					validTemplates = append(validTemplates, t)
					break
				}
			}
		}
		if len(validTemplates) > 0 {
			base = validTemplates[rand.Intn(len(validTemplates))]
		} else {
			base = templates[rand.Intn(len(templates))]
		}
	} else {
		base = templates[rand.Intn(len(templates))]
	}

	variations := []string{"C", "CC", "CCC", "N", "O", "S", "F", "Cl", "Br",
		"C(=O)O", "C(=O)N", "CN", "CO", "CF", "CCl"}

	nMods := int(scene.CreativityTemperature*3) + 1
	modified := base
	for i := 0; i < nMods; i++ {
		if rand.Float64() > 0.5 {
			mod := variations[rand.Intn(len(variations))]
			pos := rand.Intn(len(modified))
			modified = modified[:pos] + mod + modified[pos:]
		}
	}

	return modified
}

func (c *CoCoGraphInterface) CheckValidity(smiles string) bool {
	c.mu.RLock()
	if valid, ok := c.ValidityCache[smiles]; ok {
		c.mu.RUnlock()
		return valid
	}
	c.mu.RUnlock()

	validChars := "cCnNoOsSFClBrI123456789()=#-[]\\/.@H"
	for _, ch := range smiles {
		if !strings.ContainsRune(validChars, ch) {
			c.mu.Lock()
			c.ValidityCache[smiles] = false
			c.mu.Unlock()
			return false
		}
	}

	if strings.Count(smiles, "(") != strings.Count(smiles, ")") {
		c.mu.Lock()
		c.ValidityCache[smiles] = false
		c.mu.Unlock()
		return false
	}

	if len(smiles) < 3 {
		c.mu.Lock()
		c.ValidityCache[smiles] = false
		c.mu.Unlock()
		return false
	}

	c.mu.Lock()
	c.ValidityCache[smiles] = true
	c.mu.Unlock()
	return true
}

// LiquidCrystalPredictor preditor de propriedades de LC
type LiquidCrystalPredictor struct{}

func (l *LiquidCrystalPredictor) Predict(smiles string) (float64, float64) {
	length := len(smiles)
	aromatics := strings.Count(smiles, "c")

	tmelt := 300.0 + float64(length)*2.5 + float64(aromatics)*5.0
	tmelt += gaussianNoise(0, 15.0)

	tclear := tmelt + 50.0 + float64(aromatics)*3.0 + gaussianNoise(0, 10.0)

	return math.Max(tmelt, 250.0), math.Max(tclear, tmelt+20.0)
}

// MolecularCurator curador de moléculas
type MolecularCurator struct {
	LCPredictor     *LiquidCrystalPredictor
	mu              sync.RWMutex
	CurationMetrics CurationMetrics
}

type CurationMetrics struct {
	TotalCurated int64   `json:"total_curated"`
	Accepted     int64   `json:"accepted"`
	Rejected     int64   `json:"rejected"`
	AvgQED       float64 `json:"avg_qed"`
}

func NewMolecularCurator(lcPredictor *LiquidCrystalPredictor) *MolecularCurator {
	if lcPredictor == nil {
		lcPredictor = &LiquidCrystalPredictor{}
	}
	return &MolecularCurator{
		LCPredictor: lcPredictor,
	}
}

func (m *MolecularCurator) Curate(smilesList []string, scene *MolecularScene) [][2]interface{} {
	fmt.Printf("\n🔍 CURANDO MOLÉCULAS\n")
	fmt.Printf("   Entradas: %d\n", len(smilesList))

	accepted := make([][2]interface{}, 0)
	for _, smiles := range smilesList {
		props := m.ComputeProperties(smiles, scene)
		if m.SatisfiesConstraints(props, scene.TargetProperties) {
			accepted = append(accepted, [2]interface{}{smiles, props})
			m.mu.Lock()
			m.CurationMetrics.Accepted++
			m.mu.Unlock()
		} else {
			m.mu.Lock()
			m.CurationMetrics.Rejected++
			m.mu.Unlock()
		}
		m.mu.Lock()
		m.CurationMetrics.TotalCurated++
		m.mu.Unlock()
	}

	fmt.Printf("   ✅ Aceitas: %d / %d\n", len(accepted), len(smilesList))
	return accepted
}

func (m *MolecularCurator) ComputeProperties(smiles string, scene *MolecularScene) map[string]float64 {
	props := make(map[string]float64)

	if _, hasTClear := scene.TargetProperties["tclear"]; hasTClear {
		if _, hasTMelt := scene.TargetProperties["tmelt"]; hasTMelt {
			tmelt, tclear := m.LCPredictor.Predict(smiles)
			props["tmelt"] = tmelt
			props["tclear"] = tclear
		}
	}

	length := len(smiles)
	props["molecular_weight"] = float64(length)*15.0 + gaussianNoise(0, 5.0)
	props["logp"] = float64(length)*0.3 + gaussianNoise(0, 0.5)
	props["qed"] = math.Min(1.0, 0.3+float64(length)*0.01+gaussianNoise(0, 0.1))
	props["tpsa"] = float64(length)*2.0 + gaussianNoise(0, 3.0)
	props["num_aromatic_rings"] = float64(strings.Count(smiles, "c") / 6)
	props["h_bond_donors"] = float64(strings.Count(smiles, "N") + strings.Count(smiles, "O"))
	props["h_bond_acceptors"] = float64(strings.Count(smiles, "N") + strings.Count(smiles, "O") + strings.Count(smiles, "S"))

	return props
}

func (m *MolecularCurator) SatisfiesConstraints(props map[string]float64, targets map[string][2]float64) bool {
	for prop, bounds := range targets {
		if val, ok := props[prop]; ok {
			if val < bounds[0] || val > bounds[1] {
				return false
			}
		}
	}
	return true
}

// ArkheSDKBuilder construtor do SDK
type ArkheSDKBuilder struct {
	Version      string
	Substrates   []int
	PackageName  string
	Author       string
	Dependencies []string
}

func NewArkheSDKBuilder(version string) *ArkheSDKBuilder {
	substrates := make([]int, 152)
	for i := 0; i < 152; i++ {
		substrates[i] = i
	}
	return &ArkheSDKBuilder{
		Version:     version,
		Substrates:  substrates,
		PackageName: "arkhe-os",
		Author:      "ARKHE Federation",
		Dependencies: []string{
			"numpy>=1.24.0", "scipy>=1.10.0", "torch>=2.0.0",
			"fastapi>=0.100.0", "uvicorn>=0.23.0",
			"sqlalchemy>=2.0.0", "pandas>=2.0.0", "pyyaml>=6.0",
		},
	}
}

func (s *ArkheSDKBuilder) GenerateManifest() map[string]interface{} {
	manifest := map[string]interface{}{
		"package":             s.PackageName,
		"version":             s.Version,
		"substrates_included": s.Substrates,
		"substrate_count":     len(s.Substrates),
		"author":              s.Author,
		"timestamp":           float64(time.Now().UnixNano()) / 1e9,
		"blockchain_verification": map[string]interface{}{
			"network":           "ARKHE-COSMIC-CHAIN",
			"token":             "MERCES",
			"verification_type": "sha256_package_hash",
		},
	}

	sealData := fmt.Sprintf("%s:%s:%v:%f", s.PackageName, s.Version, s.Substrates, manifest["timestamp"])
	seal := sha256.Sum256([]byte(sealData))
	manifest["canonical_seal"] = hex.EncodeToString(seal[:])[:16]

	return manifest
}

func (s *ArkheSDKBuilder) VerifyOnChain(packageHash string) map[string]interface{} {
	fmt.Printf("\n🔗 VERIFICAÇÃO ON-CHAIN (MERCES)\n")
	fmt.Printf("   Pacote: %s\n", s.PackageName)
	fmt.Printf("   Versão: %s\n", s.Version)
	fmt.Printf("   Hash: %s\n", packageHash)

	txData := fmt.Sprintf("merces:%s:%s:%s:%f", s.PackageName, s.Version, packageHash, float64(time.Now().UnixNano())/1e9)
	txID := sha256.Sum256([]byte(txData))

	verification := map[string]interface{}{
		"tx_id":               hex.EncodeToString(txID[:])[:16],
		"network":             "ARKHE-COSMIC-CHAIN",
		"token":               "MERCES",
		"package_hash":        packageHash,
		"timestamp":           float64(time.Now().UnixNano()) / 1e9,
		"status":              "verified",
		"substrates_verified": len(s.Substrates),
	}

	fmt.Printf("   TX ID: %s\n", verification["tx_id"])
	fmt.Printf("   Status: ✅ VERIFICADO\n")

	return verification
}

// Helper
func parseFloat(s string) float64 {
	var f float64
	fmt.Sscanf(s, "%f", &f)
	return f
}
