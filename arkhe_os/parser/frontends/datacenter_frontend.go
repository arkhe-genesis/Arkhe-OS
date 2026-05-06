package frontends

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/arkhe-os/arkhe/parser/lfir"
)

// DataCenterFrontend implementa parsing de infraestrutura de data center para LFIR
type DataCenterFrontend struct {
	clusterName string
	parserConfig ParserConfig
}

// ParserConfig contém configuração para parsing de data center
type ParserConfig struct {
	EnableNvidiaSMI    bool
	EnableK8sQueries   bool
	EnableSlurmQueries bool
	EnableLogParsing   bool
	EnableConfigParsing bool
	ParseIntervalSec   int64
}

// NewDataCenterFrontend cria novo frontend para parsing de data centers
func NewDataCenterFrontend(clusterName string, config ParserConfig) (*DataCenterFrontend, error) {
	return &DataCenterFrontend{
		clusterName:  clusterName,
		parserConfig: config,
	}, nil
}

func (f *DataCenterFrontend) GetLanguage() string { return "datacenter" }
func (f *DataCenterFrontend) GetClusterName() string { return f.clusterName }
func (f *DataCenterFrontend) GetExtensions() []string {
	return []string{".dc", ".cluster", ".gpu", ".tpu", ".slurm", ".k8s", ".yaml", ".json", ".log"}
}

// Parse analisa fonte de dados de data center e gera LFIRGraph
func (f *DataCenterFrontend) Parse(source []byte) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	module := lfir.NewLFIRNode(lfir.LFIRModule, f.clusterName, "datacenter")
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)

	content := string(source)
	lines := strings.Split(content, "\n")

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Parsing de nvidia-smi / rocm-smi
		if f.parserConfig.EnableNvidiaSMI && strings.Count(line, ",") >= 4 {
			if err := f.parseGPUInfo(line, graph, module.ID); err != nil {
				continue
			}
		}

		// Parsing de logs de treinamento
		if f.parserConfig.EnableLogParsing && strings.Contains(line, "loss=") {
			if err := f.parseTrainingLog(line, graph, module.ID); err != nil {
				continue
			}
		}

		// Parsing de configs YAML/JSON
		if f.parserConfig.EnableConfigParsing && (strings.HasPrefix(line, "{") || strings.HasPrefix(line, "[")) {
			if err := f.parseModelConfig(line, graph, module.ID); err != nil {
				continue
			}
		}
	}

	// Se habilitado, executar queries em tempo real
	if f.parserConfig.EnableK8sQueries || f.parserConfig.EnableSlurmQueries {
		if err := f.enrichWithLiveQueries(graph, module.ID); err != nil {
			// Logar erro mas não falhar o parsing
		}
	}

	return graph, nil
}

// parseGPUInfo extrai informações de GPU de linha do nvidia-smi
func (f *DataCenterFrontend) parseGPUInfo(line string, graph *lfir.LFIRGraph, moduleID string) error {
	parts := strings.Split(line, ",")
	if len(parts) < 3 {
		return fmt.Errorf("insufficient fields in GPU line")
	}

	gpuModel := strings.TrimSpace(parts[1])
	memStr := strings.TrimSpace(parts[2])
	memMB, err := parseMemory(memStr)
	if err != nil {
		return err
	}

	// Criar nó LFIR para hardware
	gpuNode := lfir.NewLFIRNode(lfir.LFIRType, gpuModel, "datacenter")
	gpuNode.Attributes["memory_mb"] = memMB
	gpuNode.Attributes["type"] = "GPU"
	gpuNode.Attributes["parsed_at"] = time.Now().Unix()

	// Extrair campos adicionais se presentes
	if len(parts) >= 4 {
		if temp, err := extractInt(parts[3], "C"); err == nil {
			gpuNode.Attributes["temperature_c"] = temp
		}
	}
	if len(parts) >= 5 {
		if power, err := extractFloat(parts[4], "W"); err == nil {
			gpuNode.Attributes["power_draw_w"] = power
		}
	}

	graph.AddNode(gpuNode)
	graph.Link(moduleID, gpuNode.ID)
	return nil
}

// parseTrainingLog extrai métricas de treinamento de log
func (f *DataCenterFrontend) parseTrainingLog(line string, graph *lfir.LFIRGraph, moduleID string) error {
	metricsNode := lfir.NewLFIRNode(lfir.LFIROperation, "training_step", "datacenter")

	// Extrair valores numéricos com regex
	extractors := map[string]*regexp.Regexp{
		"loss":       regexp.MustCompile(`loss=([0-9.]+)`),
		"acc":        regexp.MustCompile(`acc=([0-9.]+)`),
		"grad_norm":  regexp.MustCompile(`grad_norm=([0-9.]+)`),
		"lr":         regexp.MustCompile(`lr=([0-9.e-]+)`),
		"throughput": regexp.MustCompile(`throughput=([0-9.]+)`),
	}

	for key, re := range extractors {
		if match := re.FindStringSubmatch(line); len(match) > 1 {
			if val, err := strconv.ParseFloat(match[1], 64); err == nil {
				metricsNode.Attributes[key] = val
			}
		}
	}

	// Extrair epoch se presente
	if epochRe := regexp.MustCompile(`epoch\s+(\d+)/(\d+)`); epochRe.MatchString(line) {
		match := epochRe.FindStringSubmatch(line)
		if len(match) >= 3 {
			current, _ := strconv.Atoi(match[1])
			total, _ := strconv.Atoi(match[2])
			metricsNode.Attributes["epoch_current"] = current
			metricsNode.Attributes["epoch_total"] = total
			metricsNode.Attributes["epoch_progress"] = float64(current) / float64(total)
		}
	}

	metricsNode.Attributes["parsed_at"] = time.Now().Unix()
	graph.AddNode(metricsNode)
	graph.Link(moduleID, metricsNode.ID)
	return nil
}

// parseModelConfig extrai configuração de modelo de JSON/YAML
func (f *DataCenterFrontend) parseModelConfig(line string, graph *lfir.LFIRGraph, moduleID string) error {
	var config map[string]interface{}
	if err := json.Unmarshal([]byte(line), &config); err != nil {
		return err
	}

	configNode := lfir.NewLFIRNode(lfir.LFIRModule, "model_config", "datacenter")

	// Mapear campos comuns de configuração de modelo
	commonFields := []string{
		"model_name", "batch_size", "learning_rate", "optimizer",
		"num_layers", "hidden_size", "num_heads", "dropout",
	}
	for _, field := range commonFields {
		if val, ok := config[field]; ok {
			configNode.Attributes[field] = val
		}
	}

	// Armazenar config completa como JSON string para referência
	if jsonBytes, err := json.Marshal(config); err == nil {
		configNode.Attributes["full_config_json"] = string(jsonBytes)
	}

	configNode.Attributes["parsed_at"] = time.Now().Unix()
	graph.AddNode(configNode)
	graph.Link(moduleID, configNode.ID)
	return nil
}

// enrichWithLiveQueries enriquece LFIR com queries em tempo real
func (f *DataCenterFrontend) enrichWithLiveQueries(graph *lfir.LFIRGraph, moduleID string) error {
	// Query K8s para topologia de cluster
	if f.parserConfig.EnableK8sQueries {
		if output, err := exec.Command("kubectl", "get", "nodes", "-o", "json").Output(); err == nil {
			topologyNode := lfir.NewLFIRNode(lfir.LFIRNetworkTopology, "k8s_cluster", "datacenter")
			topologyNode.Attributes["raw_output"] = string(output)
			topologyNode.Attributes["queried_at"] = time.Now().Unix()
			graph.AddNode(topologyNode)
			graph.Link(moduleID, topologyNode.ID)
		}
	}

	// Query Slurm para jobs ativos
	if f.parserConfig.EnableSlurmQueries {
		if output, err := exec.Command("scontrol", "show", "jobs").Output(); err == nil {
			jobsNode := lfir.NewLFIRNode(lfir.LFIROperation, "slurm_jobs", "datacenter")
			jobsNode.Attributes["raw_output"] = string(output)
			jobsNode.Attributes["queried_at"] = time.Now().Unix()
			graph.AddNode(jobsNode)
			graph.Link(moduleID, jobsNode.ID)
		}
	}

	return nil
}

// Helper functions
func parseMemory(s string) (int, error) {
	s = strings.TrimSpace(s)
	s = strings.ReplaceAll(s, "MiB", "")
	s = strings.ReplaceAll(s, "GiB", "")
	s = strings.ReplaceAll(s, "TiB", "")
	return strconv.Atoi(s)
}

func extractInt(s, suffix string) (int, error) {
	s = strings.TrimSpace(s)
	s = strings.TrimSuffix(s, suffix)
	return strconv.Atoi(s)
}

func extractFloat(s, suffix string) (float64, error) {
	s = strings.TrimSpace(s)
	s = strings.TrimSuffix(s, suffix)
	return strconv.ParseFloat(s, 64)
}
