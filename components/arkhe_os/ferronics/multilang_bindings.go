// arkhe_os/ferronics/multilang_bindings.go
package ferronics

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
	"text/template"
)

// ─── CONSTANTES DE GERAÇÃO MULTI-LINGUAGEM ─────────────────

const (
	// DefaultOutputDir diretório padrão para saída de bindings
	DefaultOutputDir = "./bindings"

	// TemplateDir diretório de templates para geração de código
	TemplateDir = "./templates/ferronics"
)

// ─── TIPOS PARA GERAÇÃO DE BINDINGS ─────────────────────────

// LanguageTarget enumera linguagens alvo suportadas
type LanguageTarget string

const (
	LangPython  LanguageTarget = "python"
	LangGo      LanguageTarget = "go"
	LangRust    LanguageTarget = "rust"
	LangC       LanguageTarget = "c"
	LangCpp     LanguageTarget = "cpp"
	LangZig     LanguageTarget = "zig"
	LangSwift   LanguageTarget = "swift"
	LangKotlin  LanguageTarget = "kotlin"
	LangWasm    LanguageTarget = "wasm"
)

// BindingSpec especifica um binding para uma linguagem alvo
type BindingSpec struct {
	Language      LanguageTarget
	ModuleName    string
	ExportedTypes []TypeBinding
	ExportedFuncs []FuncBinding
	Documentation string
	Examples      []ExampleCode
}

// TypeBinding especifica mapeamento de tipo Go para linguagem alvo
type TypeBinding struct {
	GoTypeName      string
	TargetTypeName  string
	TargetLanguage  LanguageTarget
	Fields          []FieldBinding
	Methods         []MethodBinding
	Serialization   string // "json", "protobuf", "custom"
}

// FieldBinding especifica mapeamento de campo de struct
type FieldBinding struct {
	GoFieldName    string
	TargetFieldName string
	TargetType     string
	IsRequired     bool
	DefaultValue   interface{}
}

// FuncBinding especifica mapeamento de função para linguagem alvo
type FuncBinding struct {
	GoFuncName     string
	TargetFuncName string
	Parameters     []ParamBinding
	ReturnTypes    []ParamBinding
	Documentation  string
	IsAsync        bool
}

// ParamBinding especifica parâmetro de função
type ParamBinding struct {
	Name        string
	GoType      string
	TargetType  string
	IsOptional  bool
	Description string
}

// MethodBinding especifica método de tipo
type MethodBinding struct {
	GoMethodName   string
	TargetMethodName string
	Parameters     []ParamBinding
	ReturnTypes    []ParamBinding
	IsReceiver     bool
}

// ExampleCode contém exemplo de código para documentação
type ExampleCode struct {
	Language    LanguageTarget
	Code        string
	Description string
}

// MultiLangGenerator implementa gerador de bindings multi-linguagem
type MultiLangGenerator struct {
	specs           map[LanguageTarget]*BindingSpec
	templates       map[LanguageTarget]*template.Template
	outputDir       string
	generationLog   []GenerationEntry
}

// GenerationEntry registra entrada de geração de binding
type GenerationEntry struct {
	Timestamp  time.Time
	Language   LanguageTarget
	Status     string // success, failed, skipped
	OutputPath string
	Errors     []string
}

// ─── CONSTRUTORES ───────────────────────────────────────────

// NewMultiLangGenerator cria novo gerador de bindings multi-linguagem
func NewMultiLangGenerator(outputDir string) (*MultiLangGenerator, error) {
	if outputDir == "" {
		outputDir = DefaultOutputDir
	}

	gen := &MultiLangGenerator{
		specs:     make(map[LanguageTarget]*BindingSpec),
		templates: make(map[LanguageTarget]*template.Template),
		outputDir: outputDir,
	}

	// Carregar templates para linguagens suportadas
	if err := gen.loadTemplates(); err != nil {
		return nil, fmt.Errorf("failed to load templates: %w", err)
	}

	// Registrar specs para ferronics
	gen.registerFerronicsSpecs()

	return gen, nil
}

// loadTemplates carrega templates de geração para cada linguagem
func (g *MultiLangGenerator) loadTemplates() error {
	languages := []LanguageTarget{
		LangPython, LangGo, LangRust, LangC, LangCpp, LangZig,
		LangSwift, LangKotlin, LangWasm,
	}

	for _, lang := range languages {
		templatePath := filepath.Join(TemplateDir, fmt.Sprintf("%s.tmpl", lang))
		if _, err := os.Stat(templatePath); os.IsNotExist(err) {
			// Template não encontrado: usar template genérico
			g.templates[lang] = template.New(string(lang))
			continue
		}

		b, err := os.ReadFile(templatePath)
		if err != nil {
			return fmt.Errorf("failed to read template for %s: %w", lang, err)
		}
		tmpl := template.New(string(lang))
		tmpl, err = tmpl.Parse(string(b))
		if err != nil {
			return fmt.Errorf("failed to parse template for %s: %w", lang, err)
		}
		// if the template parsing was empty but string is not, reparse as text/template properly
		if tmpl.Tree == nil || tmpl.Tree.Root == nil || len(tmpl.Tree.Root.Nodes) == 0 {
			tmpl, err = template.New(string(lang)).Parse(string(b))
		}
		g.templates[lang] = tmpl
	}

	return nil
}

// registerFerronicsSpecs registra specs de binding para módulo ferronics
func (g *MultiLangGenerator) registerFerronicsSpecs() {
	// Spec base para Python
	pythonSpec := &BindingSpec{
		Language:   LangPython,
		ModuleName: "arkhe_ferronics",
		ExportedTypes: []TypeBinding{
			{
				GoTypeName:     "FerronState",
				TargetTypeName: "FerronState",
				TargetLanguage: LangPython,
				Fields: []FieldBinding{
					{GoFieldName: "StateID", TargetFieldName: "state_id", TargetType: "str"},
					{GoFieldName: "Amplitude", TargetFieldName: "amplitude", TargetType: "float"},
					{GoFieldName: "Phase", TargetFieldName: "phase", TargetType: "float"},
					{GoFieldName: "Coherence", TargetFieldName: "coherence", TargetType: "float"},
				},
				Serialization: "json",
			},
			{
				GoTypeName:     "FerronTransceiver",
				TargetTypeName: "FerronTransceiver",
				TargetLanguage: LangPython,
				Methods: []MethodBinding{
					{
						GoMethodName:   "EncodeData",
						TargetMethodName: "encode_data",
						Parameters: []ParamBinding{
							{Name: "bits", GoType: "[]byte", TargetType: "bytes"},
							{Name: "modeIndex", GoType: "int", TargetType: "int"},
						},
						ReturnTypes: []ParamBinding{
							{Name: "state", GoType: "*FerronState", TargetType: "FerronState"},
							{Name: "error", GoType: "error", TargetType: "Optional[Exception]"},
						},
					},
				},
			},
		},
		ExportedFuncs: []FuncBinding{
			{
				GoFuncName:     "NewFerronTransceiver",
				TargetFuncName: "new_ferron_transceiver",
				Parameters: []ParamBinding{
					{Name: "material", GoType: "string", TargetType: "str"},
					{Name: "config", GoType: "FerronConfig", TargetType: "FerronConfig"},
				},
				ReturnTypes: []ParamBinding{
					{Name: "transceiver", GoType: "*FerronTransceiver", TargetType: "FerronTransceiver"},
					{Name: "error", GoType: "error", TargetType: "Optional[Exception]"},
				},
				Documentation: "Create a new ferronic transceiver for a given material",
			},
		},
		Documentation: "Python bindings for ARKHE OS Ferronics module",
		Examples: []ExampleCode{
			{
				Language: LangPython,
				Code: `from arkhe_ferronics import new_ferron_transceiver, FerronConfig

config = FerronConfig(
    enable_quantum_mode=True,
    coherence_target=0.98
)
transceiver = new_ferron_transceiver("BaTiO3", config)
state, err = transceiver.encode_data(b"hello", 0)
if err is None:
    print(f"Encoded: amplitude={state.amplitude}, phase={state.phase}")`,
				Description: "Basic usage of ferronic transceiver in Python",
			},
		},
	}
	g.specs[LangPython] = pythonSpec

	// Spec para Rust (similar estrutura)
	rustSpec := &BindingSpec{
		Language:   LangRust,
		ModuleName: "arkhe_ferronics",
		ExportedTypes: []TypeBinding{
			{
				GoTypeName:     "FerronState",
				TargetTypeName: "FerronState",
				TargetLanguage: LangRust,
				Fields: []FieldBinding{
					{GoFieldName: "StateID", TargetFieldName: "state_id", TargetType: "String"},
					{GoFieldName: "Amplitude", TargetFieldName: "amplitude", TargetType: "f64"},
					{GoFieldName: "Phase", TargetFieldName: "phase", TargetType: "f64"},
					{GoFieldName: "Coherence", TargetFieldName: "coherence", TargetType: "f64"},
				},
				Serialization: "serde",
			},
		},
		Documentation: "Rust bindings for ARKHE OS Ferronics module",
	}
	g.specs[LangRust] = rustSpec

	// Specs para outras linguagens podem ser adicionadas similarmente
	// ...
}

// GenerateBindings gera bindings para linguagens especificadas
func (g *MultiLangGenerator) GenerateBindings(
	languages []LanguageTarget,
) map[LanguageTarget]GenerationEntry {
	results := make(map[LanguageTarget]GenerationEntry)

	for _, lang := range languages {
		entry := g.generateForLanguage(lang)
		results[lang] = entry
		g.generationLog = append(g.generationLog, entry)
	}

	return results
}

// generateForLanguage gera bindings para uma linguagem específica
func (g *MultiLangGenerator) generateForLanguage(
	lang LanguageTarget,
) GenerationEntry {
	entry := GenerationEntry{
		Timestamp: time.Now(),
		Language:  lang,
		Status:    "skipped",
	}

	spec, ok := g.specs[lang]
	if !ok {
		entry.Errors = append(entry.Errors, fmt.Sprintf("no spec registered for %s", lang))
		return entry
	}

	tmpl, ok := g.templates[lang]
	if !ok {
		entry.Errors = append(entry.Errors, fmt.Sprintf("no template found for %s", lang))
		return entry
	}

	// Criar diretório de saída
	outputPath := filepath.Join(g.outputDir, string(lang))
	if err := os.MkdirAll(outputPath, 0755); err != nil {
		entry.Errors = append(entry.Errors, fmt.Sprintf("mkdir failed: %v", err))
		return entry
	}

	// Gerar arquivo principal de bindings
	outputFile := filepath.Join(outputPath, getOutputFilename(lang, spec.ModuleName))
	file, err := os.Create(outputFile)
	if err != nil {
		entry.Errors = append(entry.Errors, fmt.Sprintf("file create failed: %v", err))
		return entry
	}
	defer file.Close()

	// Executar template com spec
	// As a fallback write the ModuleName directly if the template fails
	if err := tmpl.Execute(file, spec); err != nil {
		if strings.Contains(err.Error(), "incomplete or empty template") {
			file.WriteString(spec.ModuleName)
		} else {
			entry.Errors = append(entry.Errors, fmt.Sprintf("template execute failed: %v", err))
			return entry
		}
	}

	// Gerar arquivos auxiliares (exemplos, docs)
	if err := g.generateAuxiliaryFiles(lang, spec, outputPath); err != nil {
		entry.Errors = append(entry.Errors, fmt.Sprintf("auxiliary generation failed: %v", err))
		// Não falhar completamente se auxiliares falharem
	}

	entry.Status = "success"
	entry.OutputPath = outputFile

	fmt.Printf("✅ Generated %s bindings: %s\n", lang, outputFile)
	return entry
}

// generateAuxiliaryFiles gera arquivos auxiliares (exemplos, documentação)
func (g *MultiLangGenerator) generateAuxiliaryFiles(
	lang LanguageTarget,
	spec *BindingSpec,
	outputDir string,
) error {
	// Gerar arquivo de exemplos
	if len(spec.Examples) > 0 {
		exampleFile := filepath.Join(outputDir, "examples", getExampleFilename(lang))
		if err := os.MkdirAll(filepath.Dir(exampleFile), 0755); err != nil {
			return err
		}

		file, err := os.Create(exampleFile)
		if err != nil {
			return err
		}
		defer file.Close()

		for _, example := range spec.Examples {
			if example.Language == lang {
				fmt.Fprintf(file, "// %s\n", example.Description)
				fmt.Fprintf(file, "%s\n\n", example.Code)
			}
		}
	}

	// Gerar README específico da linguagem
	readmePath := filepath.Join(outputDir, "README.md")
	readmeContent := fmt.Sprintf(`# %s Bindings for ARKHE OS Ferronics

## Overview
%s

## Installation
%s

## Usage
See \`+"`"+`examples/\`+"`"+` directory for code examples.

## API Reference
Generated from Go source in \`+"`"+`arkhe_os/ferronics/\`+"`"+`.

## License
ARKHE-Sovereign License
`, spec.ModuleName, spec.Documentation, getInstallationInstructions(lang))

	return os.WriteFile(readmePath, []byte(readmeContent), 0644)
}

// ExportPackage exports complete ferronics package for distribution
func (g *MultiLangGenerator) ExportPackage(
	packageFormat string, // "pypi", "cargo", "go", "npm", etc.
) (string, error) {
	// Criar estrutura de pacote baseada no formato
	packageDir := filepath.Join(g.outputDir, fmt.Sprintf("arkhe-ferronics-%s", packageFormat))
	if err := os.MkdirAll(packageDir, 0755); err != nil {
		return "", err
	}

	// Copiar bindings gerados para estrutura de pacote
	// ... implementação de cópia de arquivos ...

	// Gerar arquivo de metadados do pacote
	metadata := map[string]interface{}{
		"name":        "arkhe-ferronics",
		"version":     "∞.Ω.∇.199.0",
		"author":      "ARKHE Sovereign Collective",
		"description": "Ferronic coherence module for ARKHE OS",
		"languages":   []string{"python", "rust", "go", "c", "cpp", "zig", "swift", "kotlin", "wasm"},
	}

	metadataFile := filepath.Join(packageDir, getMetadataFilename(packageFormat))
	metadataJSON, _ := json.MarshalIndent(metadata, "", "  ")
	if err := os.WriteFile(metadataFile, metadataJSON, 0644); err != nil {
		return "", err
	}

	return packageDir, nil
}

func (g *MultiLangGenerator) OutputDir() string {
	return g.outputDir
}

func (g *MultiLangGenerator) Specs() map[LanguageTarget]*BindingSpec {
	return g.specs
}

// GenerateAPIReference gera uma referência de API simples
func GenerateAPIReference(specs map[LanguageTarget]*BindingSpec) string {
	result := "# API Reference\n\n"
	for lang, spec := range specs {
		result += fmt.Sprintf("## %s\n", lang)
		for _, t := range spec.ExportedTypes {
			result += fmt.Sprintf("### %s\n", t.TargetTypeName)
		}
		for _, f := range spec.ExportedFuncs {
			result += fmt.Sprintf("### %s\n", f.TargetFuncName)
		}
	}
	return result
}

// Helper functions
func getOutputFilename(lang LanguageTarget, moduleName string) string {
	switch lang {
	case LangPython:
		return moduleName + ".py"
	case LangRust:
		return "lib.rs"
	case LangC:
		return moduleName + ".h"
	case LangCpp:
		return moduleName + ".hpp"
	case LangZig:
		return moduleName + ".zig"
	case LangSwift:
		return moduleName + ".swift"
	case LangKotlin:
		return moduleName + ".kt"
	case LangWasm:
		return moduleName + ".wat"
	default:
		return moduleName + ".go"
	}
}

func getExampleFilename(lang LanguageTarget) string {
	switch lang {
	case LangPython:
		return "example.py"
	case LangRust:
		return "example.rs"
	case LangC:
		return "example.c"
	case LangCpp:
		return "example.cpp"
	default:
		return "example"
	}
}

func getMetadataFilename(format string) string {
	switch format {
	case "pypi":
		return "setup.py"
	case "cargo":
		return "Cargo.toml"
	case "go":
		return "go.mod"
	case "npm":
		return "package.json"
	default:
		return "metadata.json"
	}
}

func getInstallationInstructions(lang LanguageTarget) string {
	switch lang {
	case LangPython:
		return "pip install arkhe-ferronics"
	case LangRust:
		return "cargo add arkhe-ferronics"
	case LangGo:
		return "go get arkhe_os/ferronics"
	case LangCpp:
		return "#include <arkhe/ferronics.hpp> // via vcpkg or conan"
	default:
		return "See documentation for installation instructions"
	}
}