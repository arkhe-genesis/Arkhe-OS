package arkhe

// Integrar o novo parser universal na estrutura existente

// GenericParser implementa a interface LanguageFrontend para o fallback
type GenericParser struct {
	detector *LanguageDetector
}

func NewGenericParser(catalog *LanguageCatalog) *GenericParser {
	return &GenericParser{
		detector: NewLanguageDetector(catalog),
	}
}

func (p *GenericParser) GetLanguage() string {
	return "generic"
}

func (p *GenericParser) GetExtensions() []string {
	return []string{"*"}
}

func (p *GenericParser) Parse(source string) (*LFIRGraph, error) {
	// Dummy para integração rápida
	graph := NewLFIRGraph()
	module := NewLFIRNode(LFIRModule, "main_generic", "generic")
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)
	return graph, nil
}
