// parser/frontends/unity_prefab_parser.go
// Substrato 298: Parser para arquivos Unity (.prefab, .unity, .asset)
package frontends

import (
	"crypto/sha256"
	"fmt"
	"math"
	"strings"
	"time"

	"arkhe_os/parser/lfir"
	"gopkg.in/yaml.v3"
)

// UnityPrefabParser implementa o Parser para artefatos Unity
type UnityPrefabParser struct {
	ParseYAML         bool
	ParseBinary       bool
	MaxDrawCalls      int // Limite para cálculo de performance
	MissingRefPenalty float64 // Penalidade por referência quebrada
}

// NewUnityPrefabParser cria uma nova instância com configurações padrão
func NewUnityPrefabParser() *UnityPrefabParser {
	return &UnityPrefabParser{
		ParseYAML:         true,
		ParseBinary:       true,
		MaxDrawCalls:      1000,
		MissingRefPenalty: 0.5,
	}
}

func (p *UnityPrefabParser) GetLanguage() string { return "unity" }

func (p *UnityPrefabParser) GetExtensions() []string {
	return []string{".prefab", ".unity", ".asset", ".mat", ".controller", ".anim"}
}

// UnitySceneStats acumula métricas para cálculo de coerência
type UnitySceneStats struct {
	TotalGameObjects    int
	ActiveGameObjects   int
	TotalComponents     int
	MissingReferences   int
	EstimatedDrawCalls  int
	ScriptCount         int
	RendererCount       int
	ColliderCount       int
	LightCount          int
	ParticleSystemCount int
}

// Parse é o método principal do Parser
func (p *UnityPrefabParser) Parse(source []byte, filename string, metadata map[string]interface{}) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	root := lfir.NewLFIRNode(
		lfir.LFIRModule,
		fmt.Sprintf("unity_artifact_%s_%d", filename, time.Now().Unix()),
		"unity",
	)
	graph.AddNode(root)
	graph.RootNodes = append(graph.RootNodes, root.ID)

	// Detectar formato: YAML (texto) ou binário (AssetBundle)
	if p.ParseYAML && p.isYAMLFormat(source) {
		return p.parseYAMLFormat(source, graph, root.ID, filename)
	} else if p.ParseBinary {
		return p.parseBinaryFormat(source, graph, root.ID, filename)
	}

	return nil, fmt.Errorf("formato não suportado para %s", filename)
}

// isYAMLFormat detecta se o arquivo está no formato YAML legível do Unity
func (p *UnityPrefabParser) isYAMLFormat(source []byte) bool {
	// Arquivos YAML do Unity começam com "%YAML 1.1" ou "---"
	content := strings.TrimSpace(string(source[:min(100, len(source))]))
	return strings.HasPrefix(content, "%YAML") || strings.HasPrefix(content, "---") ||
		strings.Contains(content, "GameObject:") || strings.Contains(content, "m_Component:")
}

// parseYAMLFormat processa arquivos Unity no formato YAML
func (p *UnityPrefabParser) parseYAMLFormat(source []byte, graph *lfir.LFIRGraph, parentID, filename string) (*lfir.LFIRGraph, error) {
	stats := &UnitySceneStats{}

	// Parse YAML
	var doc yaml.Node
	if err := yaml.Unmarshal(source, &doc); err != nil {
		return nil, fmt.Errorf("falha ao parsear YAML: %w", err)
	}

	// Walk na árvore YAML para extrair métricas
	p.walkYAMLNode(&doc, 0, func(key, value string, depth int, node *yaml.Node) {
		p.extractUnityMetrics(key, value, depth, stats)
	})

	// Criar nós LFIR representando a estrutura da cena
	p.createLFIRNodesFromStats(stats, graph, parentID)

	// Calcular coerência da cena
	coherence := p.calculateSceneCoherence(stats)

	// Atualizar nó root com métricas
	var root *lfir.LFIRNode
	if n, ok := graph.Nodes[parentID]; ok {
		root = n
	} else {
		for _, n := range graph.Nodes {
			if n.ID == parentID {
				root = n
				break
			}
		}
	}
	if root != nil {
		root.Attributes["filename"] = filename
		root.Attributes["total_gameobjects"] = stats.TotalGameObjects
		root.Attributes["active_gameobjects"] = stats.ActiveGameObjects
		root.Attributes["total_components"] = stats.TotalComponents
		root.Attributes["missing_references"] = stats.MissingReferences
		root.Attributes["estimated_draw_calls"] = stats.EstimatedDrawCalls
		root.Attributes["script_count"] = stats.ScriptCount
		root.Attributes["renderer_count"] = stats.RendererCount
		root.Attributes["coherence_score"] = coherence
		root.Attributes["coherence_utilization"] = p.calculateUtilization(stats)
		root.Attributes["coherence_integrity"] = p.calculateIntegrity(stats)
		root.Attributes["coherence_performance"] = p.calculatePerformance(stats)
	}

	// Graph doesn't have Metrics field in the LFIRGraph structure we saw,
	// ignoring setting graph.Metrics

	return graph, nil
}

// extractUnityMetrics extrai métricas relevantes do YAML do Unity
func (p *UnityPrefabParser) extractUnityMetrics(key, value string, depth int, stats *UnitySceneStats) {
	switch key {
	case "GameObject":
		stats.TotalGameObjects++
		// Assumir que GameObjects são ativos por padrão, a menos que m_IsActive=0
		stats.ActiveGameObjects++

	case "m_IsActive", "m_Enabled":
		if value == "0" || strings.ToLower(value) == "false" {
			stats.ActiveGameObjects--
		}

	case "m_Script":
		stats.ScriptCount++
		// Detectar referências quebradas: {fileID: 0} indica script faltante
		if strings.Contains(value, "fileID: 0") && !strings.Contains(value, "guid:") {
			stats.MissingReferences++
		}

	case "m_MeshRenderer", "m_SkinnedMeshRenderer", "m_SpriteRenderer":
		stats.RendererCount++
		stats.EstimatedDrawCalls++

	case "m_BoxCollider", "m_SphereCollider", "m_CapsuleCollider", "m_MeshCollider":
		stats.ColliderCount++

	case "m_Light", "m_PointLight", "m_SpotLight", "m_DirectionalLight":
		stats.LightCount++

	case "m_ParticleSystem":
		stats.ParticleSystemCount++
		stats.EstimatedDrawCalls += 2 // Partículas geralmente custam mais draw calls
	}

	stats.TotalComponents++
}

// walkYAMLNode percorre recursivamente a árvore YAML
func (p *UnityPrefabParser) walkYAMLNode(node *yaml.Node, depth int, callback func(key, value string, depth int, node *yaml.Node)) {
	if node.Kind == yaml.MappingNode {
		for i := 0; i < len(node.Content); i += 2 {
			keyNode := node.Content[i]
			valueNode := node.Content[i+1]

			key := keyNode.Value
			value := p.getNodeValue(valueNode)

			callback(key, value, depth, valueNode)
			p.walkYAMLNode(valueNode, depth+1, callback)
		}
	} else if node.Kind == yaml.SequenceNode {
		for _, child := range node.Content {
			p.walkYAMLNode(child, depth+1, callback)
		}
	}
}

// getNodeValue extrai o valor de um nó YAML como string
func (p *UnityPrefabParser) getNodeValue(node *yaml.Node) string {
	switch node.Kind {
	case yaml.ScalarNode:
		return node.Value
	case yaml.MappingNode, yaml.SequenceNode:
		// Para nós complexos, retornar representação simplificada
		return fmt.Sprintf("{%s}", node.ShortTag())
	default:
		return ""
	}
}

// createLFIRNodesFromStats cria nós LFIR representando a estrutura da cena
func (p *UnityPrefabParser) createLFIRNodesFromStats(stats *UnitySceneStats, graph *lfir.LFIRGraph, parentID string) {
	// Criar nó agregador para GameObjects
	goContainer := lfir.NewLFIRNode(lfir.LFIRNodeTypeCollection, "gameobjects", "unity")
	goContainer.Attributes["count"] = stats.TotalGameObjects
	goContainer.Attributes["active_count"] = stats.ActiveGameObjects
	graph.AddNode(goContainer)
	graph.Link(parentID, goContainer.ID)

	// Criar nós para componentes principais
	components := []struct {
		name  string
		count int
	}{
		{"scripts", stats.ScriptCount},
		{"renderers", stats.RendererCount},
		{"colliders", stats.ColliderCount},
		{"lights", stats.LightCount},
		{"particle_systems", stats.ParticleSystemCount},
	}

	for _, comp := range components {
		if comp.count > 0 {
			node := lfir.NewLFIRNode(lfir.LFIRType, comp.name, "unity")
			node.Attributes["count"] = comp.count
			graph.AddNode(node)
			graph.Link(goContainer.ID, node.ID)
		}
	}

	// Criar nó de alerta para referências quebradas
	if stats.MissingReferences > 0 {
		alert := lfir.NewLFIRNode(lfir.LFIRNodeTypeAlert, "missing_references", "unity")
		alert.Attributes["count"] = stats.MissingReferences
		alert.Attributes["severity"] = "warning"
		graph.AddNode(alert)
		graph.Link(parentID, alert.ID)
	}
}

// calculateSceneCoherence calcula Φ_C para a cena Unity
func (p *UnityPrefabParser) calculateSceneCoherence(stats *UnitySceneStats) float64 {
	utilization := p.calculateUtilization(stats)
	integrity := p.calculateIntegrity(stats)
	performance := p.calculatePerformance(stats)

	// Combinação ponderada dos fatores
	weights := map[string]float64{
		"utilization": 0.35,
		"integrity":   0.40,
		"performance": 0.25,
	}

	coherence := weights["utilization"]*utilization +
		weights["integrity"]*integrity +
		weights["performance"]*performance

	return math.Max(0.0, math.Min(1.0, coherence))
}

func (p *UnityPrefabParser) calculateUtilization(stats *UnitySceneStats) float64 {
	if stats.TotalGameObjects == 0 {
		return 1.0
	}
	return float64(stats.ActiveGameObjects) / float64(stats.TotalGameObjects)
}

func (p *UnityPrefabParser) calculateIntegrity(stats *UnitySceneStats) float64 {
	// Decaimento exponencial com número de referências quebradas
	return math.Exp(-p.MissingRefPenalty * float64(stats.MissingReferences))
}

func (p *UnityPrefabParser) calculatePerformance(stats *UnitySceneStats) float64 {
	if p.MaxDrawCalls == 0 {
		return 1.0
	}
	score := 1.0 - float64(stats.EstimatedDrawCalls)/float64(p.MaxDrawCalls)
	return math.Max(0.0, score)
}

// parseBinaryFormat processa arquivos binários do Unity (AssetBundles)
func (p *UnityPrefabParser) parseBinaryFormat(source []byte, graph *lfir.LFIRGraph, parentID, filename string) (*lfir.LFIRGraph, error) {
	// Header simplificado do AssetBundle (formato real é mais complexo)
	if len(source) < 24 {
		return nil, fmt.Errorf("arquivo binário muito pequeno para ser um AssetBundle válido")
	}

	// Ler signature (primeiros 7 bytes: "UnityFS" ou similar)
	signature := string(source[:7])

	var root *lfir.LFIRNode
	if n, ok := graph.Nodes[parentID]; ok {
		root = n
	} else {
		for _, n := range graph.Nodes {
			if n.ID == parentID {
				root = n
				break
			}
		}
	}

	if root != nil {
		root.Attributes["format"] = "unity_asset_bundle"
		root.Attributes["signature"] = signature
		root.Attributes["file_size_bytes"] = len(source)

		// Calcular hash de integridade
		contentHash := fmt.Sprintf("%x", sha256.Sum256(source))
		root.Attributes["content_hash"] = contentHash[:16]

		// Coerência baseada em integridade do arquivo
		integrityScore := 0.85 // Baseline para bundles válidos
		if strings.Contains(signature, "UnityFS") {
			integrityScore = 0.95
		}

		root.Attributes["coherence_score"] = integrityScore
	}

	return graph, nil
}

// Helper: min function para Go <1.21
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
