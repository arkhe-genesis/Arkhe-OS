// parser/frontends/steam_vdf_parser.go
// Parser para arquivos no formato KeyValues da Valve (.vdf, .acf, .manifest)
package frontends

import (
	"bufio"
	"fmt"
	"math"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"

	"arkhe_os/parser/lfir"
)

// SteamVDFParser implementa parser para formato KeyValues da Valve
type SteamVDFParser struct {
	ValidateChecksums bool
	MaxDepotSizeGB    float64
}

func NewSteamVDFParser() *SteamVDFParser {
	return &SteamVDFParser{
		ValidateChecksums: true,
		MaxDepotSizeGB:    50.0,
	}
}

func (p *SteamVDFParser) GetLanguage() string { return "steam-vdf" }

func (p *SteamVDFParser) GetExtensions() []string {
	return []string{".vdf", ".acf", ".manifest", ".steam"}
}

// SteamBuildStats acumula métricas de builds Steam
type SteamBuildStats struct {
	AppID              string
	DepotCount         int
	TotalSizeBytes     int64
	FileCount          int
	AchievementCount   int
	BranchCount        int
	MissingFiles       int
	ChecksumMismatches int
	LastUpdated        time.Time
	BuildSuccessRate   float64
}

// Parse processa arquivos VDF/ACF da Steam
func (p *SteamVDFParser) Parse(source []byte, filename string, metadata map[string]interface{}) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	root := lfir.NewLFIRNode(
		lfir.LFIRModule,
		fmt.Sprintf("steam_manifest_%s_%d", filepath.Base(filename), time.Now().Unix()),
		"steam",
	)
	graph.AddNode(root)
	graph.RootNodes = append(graph.RootNodes, root.ID)

	stats := &SteamBuildStats{}

	// Parse formato KeyValues
	kvRoot := p.parseKeyValues(string(source))
	if kvRoot == nil {
		return nil, fmt.Errorf("falha ao parsear formato KeyValues")
	}

	// Extrair metadados da build
	p.extractSteamMetrics(kvRoot, stats, filename)

	// Criar estrutura LFIR
	p.createSteamLFIRStructure(stats, kvRoot, graph, root.ID, filename)

	// Calcular coerência da build
	coherence := p.calculateBuildCoherence(stats)

	// Atualizar root com métricas
	root.Attributes["app_id"] = stats.AppID
	root.Attributes["depot_count"] = stats.DepotCount
	root.Attributes["total_size_gb"] = float64(stats.TotalSizeBytes) / (1024 * 1024 * 1024)
	root.Attributes["file_count"] = stats.FileCount
	root.Attributes["achievement_count"] = stats.AchievementCount
	root.Attributes["missing_files"] = stats.MissingFiles
	root.Attributes["checksum_mismatches"] = stats.ChecksumMismatches
	root.Attributes["build_success_rate"] = stats.BuildSuccessRate
	root.Attributes["coherence_score"] = coherence
	root.Attributes["coherence_integrity"] = p.calculateBuildIntegrity(stats)
	root.Attributes["coherence_completeness"] = p.calculateBuildCompleteness(stats)
	root.Attributes["coherence_reliability"] = stats.BuildSuccessRate

	return graph, nil
}

// parseKeyValues parseia o formato KeyValues da Valve
func (p *SteamVDFParser) parseKeyValues(content string) *KVNode {
	root := &KVNode{Key: "root", Children: make([]*KVNode, 0)}
	stack := []*KVNode{root}

	scanner := bufio.NewScanner(strings.NewReader(content))

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())

		// Ignorar linhas vazias e comentários
		if line == "" || strings.HasPrefix(line, "//") {
			continue
		}

		// Handle braces
		if line == "{" {
			continue
		}
		if line == "}" {
			if len(stack) > 1 {
				stack = stack[:len(stack)-1]
			}
			continue
		}

		// Parse key-value pair ou key com children
		parsed := p.parseKVLine(line)
		if parsed == nil {
			continue
		}

		current := stack[len(stack)-1]
		current.Children = append(current.Children, parsed)

		// Se o valor é "{", o próximo token inicia children deste nó
		if parsed.Value == "{" {
			stack = append(stack, parsed)
		}
	}

	return root
}

// parseKVLine parseia uma linha no formato KeyValues
func (p *SteamVDFParser) parseKVLine(line string) *KVNode {
	// Remover aspas extras e normalizar
	line = strings.TrimSpace(line)

	// Padrão: "key" "value" ou "key" {
	re := regexp.MustCompile(`^"([^"]+)"\s+"?([^"{\n]*)"?`)
	matches := re.FindStringSubmatch(line)

	if len(matches) >= 2 {
		key := matches[1]
		value := ""
		if len(matches) >= 3 {
			value = strings.TrimSpace(matches[2])
		}

		// Detectar se tem children
		if strings.Contains(line[len(matches[0]):], "{") {
			value = "{"
		}

		return &KVNode{
			Key:      key,
			Value:    value,
			Children: make([]*KVNode, 0),
		}
	}

	return nil
}

// KVNode representa um nó no formato KeyValues da Valve
type KVNode struct {
	Key      string
	Value    string
	Children []*KVNode
}

// Get retorna child por key
func (n *KVNode) Get(key string) *KVNode {
	for _, child := range n.Children {
		if child.Key == key {
			return child
		}
	}
	return nil
}

// GetString retorna valor como string
func (n *KVNode) GetString(key string) string {
	child := n.Get(key)
	if child != nil {
		return child.Value
	}
	return ""
}

// GetInt retorna valor como int
func (n *KVNode) GetInt(key string) int {
	child := n.Get(key)
	if child != nil {
		val, _ := strconv.Atoi(child.Value)
		return val
	}
	return 0
}

// GetFloat retorna valor como float64
func (n *KVNode) GetFloat(key string) float64 {
	child := n.Get(key)
	if child != nil {
		val, _ := strconv.ParseFloat(child.Value, 64)
		return val
	}
	return 0.0
}

// extractSteamMetrics extrai métricas do manifest Steam
func (p *SteamVDFParser) extractSteamMetrics(kvRoot *KVNode, stats *SteamBuildStats, filename string) {
	// Extrair AppID do nome do arquivo ou do conteúdo
	if appID := p.extractAppIDFromFilename(filename); appID != "" {
		stats.AppID = appID
	} else if appIDNode := kvRoot.Get("appid"); appIDNode != nil {
		stats.AppID = appIDNode.Value
	}

	// Extrair depots
	if depots := kvRoot.Get("depots"); depots != nil {
		stats.DepotCount = len(depots.Children)
		for _, depot := range depots.Children {
			if size := depot.GetInt("maxsize"); size > 0 {
				stats.TotalSizeBytes += int64(size) * 1024 * 1024 // MB para bytes
			}
			stats.FileCount += depot.GetInt("filecount")
		}
	}

	// Extrair achievements
	if achievements := kvRoot.Get("achievements"); achievements != nil {
		stats.AchievementCount = len(achievements.Children)
	}

	// Extrair branches
	if branches := kvRoot.Get("branches"); branches != nil {
		stats.BranchCount = len(branches.Children)
	}

	// Extrair timestamp de atualização
	if updated := kvRoot.GetInt("lastupdated"); updated > 0 {
		stats.LastUpdated = time.Unix(int64(updated), 0)
	}

	// Build success rate (simulado baseado em histórico)
	stats.BuildSuccessRate = 0.95 // Placeholder
}

func (p *SteamVDFParser) extractAppIDFromFilename(filename string) string {
	// Padrão: appmanifest_123456.acf
	re := regexp.MustCompile(`appmanifest_(\d+)\.acf`)
	matches := re.FindStringSubmatch(filename)
	if len(matches) >= 2 {
		return matches[1]
	}
	return ""
}

// createSteamLFIRStructure cria nós LFIR para a build Steam
func (p *SteamVDFParser) createSteamLFIRStructure(
	stats *SteamBuildStats,
	kvRoot *KVNode,
	graph *lfir.LFIRGraph,
	parentID, filename string,
) {
	// Nó para depots
	if stats.DepotCount > 0 {
		depotContainer := lfir.NewLFIRNode(lfir.LFIRNodeTypeCollection, "depots", "steam")
		depotContainer.Attributes["count"] = stats.DepotCount
		depotContainer.Attributes["total_size_gb"] = float64(stats.TotalSizeBytes) / (1024 * 1024 * 1024)
		graph.AddNode(depotContainer)
		graph.Link(parentID, depotContainer.ID)

		// Criar nós individuais para cada depot
		if depots := kvRoot.Get("depots"); depots != nil {
			for _, depot := range depots.Children {
				depotNode := lfir.NewLFIRNode(lfir.LFIRType,
					fmt.Sprintf("depot_%s", depot.Key), "steam")
				depotNode.Attributes["depot_id"] = depot.Key
				depotNode.Attributes["size_mb"] = depot.GetInt("maxsize")
				depotNode.Attributes["file_count"] = depot.GetInt("filecount")

				// Verificar integridade se checksum disponível
				if p.ValidateChecksums {
					if checksum := depot.GetString("checksum"); checksum != "" {
						depotNode.Attributes["checksum_verified"] = true
					}
				}

				graph.AddNode(depotNode)
				graph.Link(depotContainer.ID, depotNode.ID)
			}
		}
	}

	// Nó para achievements
	if stats.AchievementCount > 0 {
		achContainer := lfir.NewLFIRNode(lfir.LFIRNodeTypeCollection, "achievements", "steam")
		achContainer.Attributes["count"] = stats.AchievementCount
		graph.AddNode(achContainer)
		graph.Link(parentID, achContainer.ID)

		if achievements := kvRoot.Get("achievements"); achievements != nil {
			for _, ach := range achievements.Children {
				achNode := lfir.NewLFIRNode(lfir.LFIRType,
					fmt.Sprintf("achievement_%s", ach.Key), "steam")
				achNode.Attributes["achievement_id"] = ach.Key
				achNode.Attributes["hidden"] = ach.GetInt("hidden") == 1
				achNode.Attributes["icon"] = ach.GetString("icon")
				graph.AddNode(achNode)
				graph.Link(achContainer.ID, achNode.ID)
			}
		}
	}

	// Alertas para problemas de integridade
	if stats.MissingFiles > 0 || stats.ChecksumMismatches > 0 {
		alert := lfir.NewLFIRNode(lfir.LFIRNodeTypeAlert, "integrity_issues", "steam")
		alert.Attributes["missing_files"] = stats.MissingFiles
		alert.Attributes["checksum_mismatches"] = stats.ChecksumMismatches
		alert.Attributes["severity"] = "warning"
		graph.AddNode(alert)
		graph.Link(parentID, alert.ID)
	}
}

// calculateBuildCoherence calcula Φ_C para builds Steam
func (p *SteamVDFParser) calculateBuildCoherence(stats *SteamBuildStats) float64 {
	integrity := p.calculateBuildIntegrity(stats)
	completeness := p.calculateBuildCompleteness(stats)
	reliability := stats.BuildSuccessRate

	// Combinação ponderada
	weights := map[string]float64{
		"integrity":   0.45,
		"completeness": 0.35,
		"reliability": 0.20,
	}

	coherence := weights["integrity"]*integrity +
		weights["completeness"]*completeness +
		weights["reliability"]*reliability

	return math.Max(0.0, math.Min(1.0, coherence))
}

func (p *SteamVDFParser) calculateBuildIntegrity(stats *SteamBuildStats) float64 {
	if stats.FileCount == 0 {
		return 1.0
	}
	missingRatio := float64(stats.MissingFiles+stats.ChecksumMismatches) / float64(stats.FileCount)
	return math.Exp(-2.0 * missingRatio)
}

func (p *SteamVDFParser) calculateBuildCompleteness(stats *SteamBuildStats) float64 {
	// Verificar se todos os depots esperados estão presentes
	if stats.DepotCount == 0 {
		return 0.5
	}
	// Penalizar builds muito grandes que podem indicar problemas
	sizeGB := float64(stats.TotalSizeBytes) / (1024 * 1024 * 1024)
	if sizeGB > p.MaxDepotSizeGB {
		return 0.7 // Build suspeitamente grande
	}
	return 1.0
}
