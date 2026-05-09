// datacenter_frontend.go
package arkhe

import (
    "strconv"
    "strings"
)

type DataCenterFrontend struct {
    clusterName string
}

func NewDataCenterFrontend(clusterName string) (*DataCenterFrontend, error) {
    return &DataCenterFrontend{clusterName: clusterName}, nil
}

func (f *DataCenterFrontend) GetLanguage() string { return "datacenter" }
func (f *DataCenterFrontend) GetExtensions() []string {
    return []string{".dc", ".cluster", ".gpu", ".tpu", ".slurm", ".k8s"}
}

// Parse analisa a saída de comandos de monitoramento e arquivos de configuração.
func (f *DataCenterFrontend) Parse(source string) (*LFIRGraph, error) {
    graph := NewLFIRGraph()
    module := NewLFIRNode(LFIRModule, f.clusterName, "datacenter")
    graph.AddNode(module)
    graph.RootNodes = append(graph.RootNodes, module.ID)

    content := source
    lines := strings.Split(content, "\n")

    for _, line := range lines {
        line = strings.TrimSpace(line)
        if line == "" || strings.HasPrefix(line, "#") {
            continue
        }

        // Exemplo de parsing de linha do nvidia-smi:
        // 0, Tesla V100-SXM2-32GB, 32510 MiB, 80 C, 150 W, 300 W
        if strings.Count(line, ",") >= 4 {
            parts := strings.Split(line, ",")
            if len(parts) >= 3 {
                gpuModel := strings.TrimSpace(parts[1])
                memStr := strings.TrimSpace(parts[2])
                memMB, _ := parseMemory(memStr)

                gpuNode := NewLFIRNode(LFIRType, gpuModel, "datacenter")
                if gpuNode.Attributes == nil {
                    gpuNode.Attributes = make(map[string]interface{})
                }
                gpuNode.Attributes["memory_mb"] = memMB
                gpuNode.Attributes["type"] = "GPU"
                graph.AddNode(gpuNode)
                graph.Link(module.ID, gpuNode.ID)
            }
        }

        // Exemplo de linha de log de treinamento:
        // [epoch 12/100] loss=0.342, acc=0.891, grad_norm=1.23, time=2.34s
        if strings.Contains(line, "loss=") && strings.Contains(line, "epoch") {
            metricsNode := NewLFIRNode(LFIROperation, "training_step", "datacenter")
            if metricsNode.Attributes == nil {
                metricsNode.Attributes = make(map[string]interface{})
            }
            // Extrair valores numéricos
            if loss, ok := extractFloat(line, "loss="); ok {
                metricsNode.Attributes["loss"] = loss
            }
            if acc, ok := extractFloat(line, "acc="); ok {
                metricsNode.Attributes["accuracy"] = acc
            }
            graph.AddNode(metricsNode)
            graph.Link(module.ID, metricsNode.ID)
        }
    }

    return graph, nil
}

func parseMemory(s string) (int, error) {
    s = strings.Replace(s, "MiB", "", 1)
    s = strings.Replace(s, "GiB", "", 1)
    s = strings.TrimSpace(s)
    return strconv.Atoi(s)
}

func extractFloat(line, prefix string) (float64, bool) {
    idx := strings.Index(line, prefix)
    if idx == -1 {
        return 0, false
    }
    rest := line[idx+len(prefix):]
    end := strings.IndexAny(rest, " ,\t\n]")
    if end == -1 {
        end = len(rest)
    }
    val, err := strconv.ParseFloat(rest[:end], 64)
    return val, err == nil
}
