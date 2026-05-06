// kernel_frontend.go — Substrato 220
package frontends

import (
	"bufio"
	"fmt"
	"regexp"
	"strings"
	"time"

	"arkhe/parser/lfir"
)

type KernelFrontend struct {
	version string // versão do kernel, ex: "6.6.0"
	arch    string // arquitetura, ex: "x86_64"
}

func NewKernelFrontend(version, arch string) (*KernelFrontend, error) {
	return &KernelFrontend{version: version, arch: arch}, nil
}

func (f *KernelFrontend) GetLanguage() string { return "kernel" }
func (f *KernelFrontend) GetExtensions() []string {
	return []string{".c", ".h", ".kconfig", ".config", ".kallsyms", ".modules", ".cmdline", ".ksym"}
}

// Parse analisa arquivos de código e informações do kernel.
func (f *KernelFrontend) Parse(source []byte) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	module := lfir.NewLFIRNode(lfir.LFIRModule, fmt.Sprintf("kernel-%s-%s", f.version, f.arch), "kernel")
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)

	content := string(source)

	// Detectar o tipo de conteúdo baseado em palavras-chave e encaminhar
	if strings.Contains(content, "sys_call_table") || strings.Contains(content, "SYSCALL_DEFINE") || strings.Contains(content, "asmlinkage") {
		return f.parseKernelSource(content, graph, module.ID)
	}
	if strings.Contains(content, "T ") && strings.Contains(content, "t ") && strings.Contains(content, "0000000000") {
		return f.parseKallsyms(content, graph, module.ID)
	}
	if strings.Contains(content, "Module") && strings.Contains(content, "Size") && strings.Contains(content, "Used by") {
		return f.parseLsmod(content, graph, module.ID)
	}
	if strings.Contains(content, "CONFIG_") && (strings.Contains(content, "=y") || strings.Contains(content, "=m") || strings.Contains(content, "is not set")) {
		return f.parseDotConfig(content, graph, module.ID)
	}
	if strings.Contains(content, "Kconfig") && strings.Contains(content, "menuconfig") {
		return f.parseKconfig(content, graph, module.ID)
	}
	if strings.Contains(content, "BOOT_IMAGE") || strings.Contains(content, "root=") {
		return f.parseCmdline(content, graph, module.ID)
	}

	// Fallback genérico
	for _, line := range strings.Split(content, "\n") {
		if line = strings.TrimSpace(line); line == "" {
			continue
		}
		eventNode := lfir.NewLFIRNode(lfir.LFIRMetadata, fmt.Sprintf("kern_%d", time.Now().UnixNano()), "kernel")
		eventNode.Attributes["message"] = line
		eventNode.Attributes["type"] = "generic_kernel_event"
		graph.AddNode(eventNode)
		graph.Link(module.ID, eventNode.ID)
	}
	return graph, nil
}

// parseKernelSource analisa código C do kernel, extraindo funções e syscalls.
func (f *KernelFrontend) parseKernelSource(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	// Detectar SYSCALL_DEFINEn macros
	syscallRe := regexp.MustCompile(`SYSCALL_DEFINE(\d)\((\w+),\s*([^)]+)\)`)
	for _, match := range syscallRe.FindAllStringSubmatch(content, -1) {
		nargs := match[1]
		name := match[2]
		// match[3] são os argumentos
		syscallNode := lfir.NewLFIRNode(lfir.LFIROperation, "sys_"+name, "kernel")
		syscallNode.Attributes["type"] = "syscall"
		syscallNode.Attributes["name"] = name
		syscallNode.Attributes["nargs"] = nargs
		graph.AddNode(syscallNode)
		graph.Link(parentID, syscallNode.ID)
	}

	// Detectar initcalls (module_init, late_initcall, etc.)
	initcallRe := regexp.MustCompile(`(\w+_initcall)\((\w+)\)`)
	for _, match := range initcallRe.FindAllStringSubmatch(content, -1) {
		initcallNode := lfir.NewLFIRNode(lfir.LFIROperation, match[2], "kernel")
		initcallNode.Attributes["type"] = "initcall"
		initcallNode.Attributes["level"] = match[1]
		graph.AddNode(initcallNode)
		graph.Link(parentID, initcallNode.ID)
	}

	// Detectar structs do kernel (ex: struct task_struct)
	structRe := regexp.MustCompile(`struct\s+(\w+)\s*\{`)
	for _, match := range structRe.FindAllStringSubmatch(content, -1) {
		structNode := lfir.NewLFIRNode(lfir.LFIRType, match[1], "kernel")
		structNode.Attributes["type"] = "kernel_struct"
		graph.AddNode(structNode)
		graph.Link(parentID, structNode.ID)
	}

	return graph, nil
}

// parseKallsyms analisa /proc/kallsyms, extraindo símbolos do kernel.
func (f *KernelFrontend) parseKallsyms(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	scanner := bufio.NewScanner(strings.NewReader(content))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		fields := strings.Fields(line)
		if len(fields) < 3 {
			continue
		}
		addr := fields[0]
		typ := fields[1]
		name := fields[2]

		symbolNode := lfir.NewLFIRNode(lfir.LFIROperation, name, "kernel")
		symbolNode.Attributes["type"] = "kernel_symbol"
		symbolNode.Attributes["address"] = addr
		symbolNode.Attributes["symbol_type"] = typ // T=text, t=local text, D=data, etc.
		graph.AddNode(symbolNode)
		graph.Link(parentID, symbolNode.ID)
	}
	return graph, nil
}

// parseLsmod analisa saída de lsmod, mapeando módulos carregados.
func (f *KernelFrontend) parseLsmod(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	scanner := bufio.NewScanner(strings.NewReader(content))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		fields := strings.Fields(line)
		if len(fields) < 3 {
			continue
		}
		modName := fields[0]
		modSize := fields[1]
		usedBy := ""
		if len(fields) > 3 {
			usedBy = strings.Join(fields[3:], ",")
		}

		modNode := lfir.NewLFIRNode(lfir.LFIRType, modName, "kernel")
		modNode.Attributes["type"] = "kernel_module"
		modNode.Attributes["size"] = modSize
		modNode.Attributes["dependencies"] = usedBy
		graph.AddNode(modNode)
		graph.Link(parentID, modNode.ID)
	}
	return graph, nil
}

// parseDotConfig analisa .config, mapeando opções de compilação.
func (f *KernelFrontend) parseDotConfig(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	scanner := bufio.NewScanner(strings.NewReader(content))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		if strings.HasPrefix(line, "#") && strings.Contains(line, "is not set") {
			// e.g. # CONFIG_FOO is not set
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				configName := parts[1]
				configNode := lfir.NewLFIRNode(lfir.LFIRMetadata, configName, "kernel")
				configNode.Attributes["type"] = "kernel_config"
				configNode.Attributes["value"] = "n"
				graph.AddNode(configNode)
				graph.Link(parentID, configNode.ID)
			}
			continue
		}

		if strings.HasPrefix(line, "#") {
			continue
		}

		if strings.Contains(line, "=y") || strings.Contains(line, "=m") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				configNode := lfir.NewLFIRNode(lfir.LFIRMetadata, parts[0], "kernel")
				configNode.Attributes["type"] = "kernel_config"
				configNode.Attributes["value"] = parts[1]
				graph.AddNode(configNode)
				graph.Link(parentID, configNode.ID)
			}
		}
	}
	return graph, nil
}

// parseKconfig analisa arquivos Kconfig, mapeando opções e dependências.
func (f *KernelFrontend) parseKconfig(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	scanner := bufio.NewScanner(strings.NewReader(content))
	var currentConfig string
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.HasPrefix(line, "config ") {
			currentConfig = strings.TrimSpace(strings.TrimPrefix(line, "config "))
		} else if strings.HasPrefix(line, "bool ") || strings.HasPrefix(line, "tristate ") {
			if currentConfig != "" {
				configNode := lfir.NewLFIRNode(lfir.LFIRMetadata, currentConfig, "kernel")
				configNode.Attributes["type"] = "kconfig_option"

				prompt := ""
				firstIdx := strings.Index(line, "\"")
				lastIdx := strings.LastIndex(line, "\"")
				if firstIdx != -1 && lastIdx != -1 && firstIdx < lastIdx {
					prompt = line[firstIdx+1 : lastIdx]
				}
				configNode.Attributes["prompt"] = strings.TrimSpace(prompt)
				graph.AddNode(configNode)
				graph.Link(parentID, configNode.ID)
			}
		}
	}
	return graph, nil
}

// parseCmdline analisa /proc/cmdline, mapeando parâmetros de boot.
func (f *KernelFrontend) parseCmdline(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	params := strings.Fields(content)
	for _, param := range params {
		parts := strings.SplitN(param, "=", 2)
		bootNode := lfir.NewLFIRNode(lfir.LFIRMetadata, parts[0], "kernel")
		bootNode.Attributes["type"] = "boot_param"
		if len(parts) == 2 {
			bootNode.Attributes["value"] = parts[1]
		}
		graph.AddNode(bootNode)
		graph.Link(parentID, bootNode.ID)
	}
	return graph, nil
}
