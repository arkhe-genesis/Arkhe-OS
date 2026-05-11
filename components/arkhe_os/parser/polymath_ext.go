package arkhe

import (


	"fmt"
	"strings"

	sitter "github.com/smacker/go-tree-sitter"
	"github.com/smacker/go-tree-sitter/csharp"
	"github.com/smacker/go-tree-sitter/cpp"
)

// ============================================================
// C# Frontend
// ============================================================

type CSharpFrontend struct {
	parser *sitter.Parser
	lang   *sitter.Language
}

func NewCSharpFrontend() (*CSharpFrontend, error) {
	parser := sitter.NewParser()
	parser.SetLanguage(csharp.GetLanguage())
	return &CSharpFrontend{parser: parser}, nil
}

func (f *CSharpFrontend) GetLanguage() string { return "csharp" }
func (f *CSharpFrontend) GetExtensions() []string { return []string{".cs"} }

func (f *CSharpFrontend) Parse(source string) (*LFIRGraph, error) {
	sourceBytes := []byte(source)
	tree, err := f.parser.ParseCtx(nil, nil, sourceBytes)
	if err != nil {
		return nil, fmt.Errorf("csharp parse error: %w", err)
	}
	root := tree.RootNode()
	if root.HasError() {
		return nil, fmt.Errorf("csharp syntax error")
	}

	graph := NewLFIRGraph()
	module := NewLFIRNode(LFIRModule, "main_cs", "csharp")
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)

	// Percorrer AST e extrair tipos e funções
	walkTreeSitterCSharp(root, sourceBytes, graph, module)

	return graph, nil
}

func walkTreeSitterCSharp(node *sitter.Node, sourceBytes []byte, graph *LFIRGraph, module *LFIRNode) {
	switch node.Type() {
	case "namespace_declaration", "class_declaration", "struct_declaration", "interface_declaration":
		nameNode := findChild(node, "name")
		if nameNode != nil {
			name := sourceBytes[nameNode.StartByte():nameNode.EndByte()]
			lfNode := NewLFIRNode(LFIRType, string(name), "csharp")
			lfNode.Attributes["line"] = int(node.StartPoint().Row) + 1
			lfNode.Attributes["tree_sitter_type"] = node.Type()
			graph.AddNode(lfNode)
			graph.Link(module.ID, lfNode.ID)
		}
	case "method_declaration", "constructor_declaration", "destructor_declaration":
		nameNode := findChild(node, "name")
		if nameNode != nil {
			name := string(sourceBytes[nameNode.StartByte():nameNode.EndByte()])
			lfNode := NewLFIRNode(LFIRFunction, name, "csharp")
			lfNode.Attributes["line"] = int(node.StartPoint().Row) + 1
			lfNode.Attributes["tree_sitter_type"] = node.Type()
			graph.AddNode(lfNode)
			graph.Link(module.ID, lfNode.ID)
		}
	}

	for i := 0; i < int(node.ChildCount()); i++ {
		walkTreeSitterCSharp(node.Child(i), sourceBytes, graph, module)
	}
}

func findChild(node *sitter.Node, childType string) *sitter.Node {
	for i := 0; i < int(node.ChildCount()); i++ {
		child := node.Child(i)
		if child.Type() == childType {
			return child
		}
	}
	return nil
}

// ============================================================
// C++ Frontend
// ============================================================

type CppFrontend struct {
	parser *sitter.Parser
}

func NewCppFrontend() (*CppFrontend, error) {
	parser := sitter.NewParser()
	parser.SetLanguage(cpp.GetLanguage())
	return &CppFrontend{parser: parser}, nil
}

func (f *CppFrontend) GetLanguage() string { return "cpp" }
func (f *CppFrontend) GetExtensions() []string { return []string{".cpp", ".cc", ".cxx", ".hpp", ".h"} }

func (f *CppFrontend) Parse(source string) (*LFIRGraph, error) {
	sourceBytes := []byte(source)
	tree, err := f.parser.ParseCtx(nil, nil, sourceBytes)
	if err != nil {
		return nil, fmt.Errorf("cpp parse error: %w", err)
	}
	root := tree.RootNode()
	if root.HasError() {
		return nil, fmt.Errorf("cpp syntax error")
	}

	graph := NewLFIRGraph()
	module := NewLFIRNode(LFIRModule, "main_cpp", "cpp")
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)

	walkTreeSitterCpp(root, sourceBytes, graph, module)

	return graph, nil
}

func walkTreeSitterCpp(node *sitter.Node, sourceBytes []byte, graph *LFIRGraph, module *LFIRNode) {
	switch node.Type() {
	case "function_definition", "declaration":
		if funcName := extractCPPFunctionName(node, sourceBytes); funcName != "" {
			lfNode := NewLFIRNode(LFIRFunction, funcName, "cpp")
			lfNode.Attributes["line"] = int(node.StartPoint().Row) + 1
			lfNode.Attributes["tree_sitter_type"] = node.Type()
			graph.AddNode(lfNode)
			graph.Link(module.ID, lfNode.ID)
		}
	case "class_specifier", "struct_specifier":
		if nameNode := findChild(node, "name"); nameNode != nil {
			name := string(sourceBytes[nameNode.StartByte():nameNode.EndByte()])
			lfNode := NewLFIRNode(LFIRType, name, "cpp")
			lfNode.Attributes["line"] = int(node.StartPoint().Row) + 1
			lfNode.Attributes["tree_sitter_type"] = node.Type()
			graph.AddNode(lfNode)
			graph.Link(module.ID, lfNode.ID)
		}
	}

	for i := 0; i < int(node.ChildCount()); i++ {
		walkTreeSitterCpp(node.Child(i), sourceBytes, graph, module)
	}
}


func extractCPPFunctionName(node *sitter.Node, source []byte) string {
	for i := 0; i < int(node.ChildCount()); i++ {
		child := node.Child(i)
		if child.Type() == "function_declarator" {
			for j := 0; j < int(child.ChildCount()); j++ {
				decl := child.Child(j)
				if decl.Type() == "identifier" {
					return string(source[decl.StartByte():decl.EndByte()])
				}
			}
		}
	}
	return ""
}

// ============================================================
// C# Backend
// ============================================================

type CSharpBackend struct{}

func NewCSharpBackend() *CSharpBackend { return &CSharpBackend{} }
func (b *CSharpBackend) GetTargetLanguage() string { return "csharp" }

func (b *CSharpBackend) Generate(graph *LFIRGraph) (string, error) {
	var out strings.Builder
	out.WriteString("// Generated by ARKHE Parser — C# Target\n")
	out.WriteString("using System;\n\n")

	for _, node := range graph.Nodes {
		switch node.Type {
		case LFIRType:
			// Mapear tipo para C#: class, struct, interface
			kind, _ := node.Attributes["tree_sitter_type"].(string)
			if strings.Contains(kind, "interface") {
				out.WriteString(fmt.Sprintf("public interface %s {\n", pascal(node.Name)))
				out.WriteString("}\n\n")
			} else if strings.Contains(kind, "struct") && !strings.Contains(kind, "class") {
				out.WriteString(fmt.Sprintf("public struct %s {\n", pascal(node.Name)))
				out.WriteString("}\n\n")
			} else {
				out.WriteString(fmt.Sprintf("public class %s {\n", pascal(node.Name)))
				out.WriteString("}\n\n")
			}
		case LFIRFunction:
			// Gerar método público
			out.WriteString(fmt.Sprintf("public void %s() {\n", pascal(node.Name)))
			out.WriteString("    // TODO: Implement method body\n")
			out.WriteString("}\n\n")
		}
	}
	return out.String(), nil
}

func pascal(s string) string {
	if len(s) == 0 {
		return s
	}
	return strings.ToUpper(s[:1]) + s[1:]
}

// ============================================================
// C++ Backend
// ============================================================

type CppBackend struct{}

func NewCppBackend() *CppBackend { return &CppBackend{} }
func (b *CppBackend) GetTargetLanguage() string { return "cpp" }

func (b *CppBackend) Generate(graph *LFIRGraph) (string, error) {
	var out strings.Builder
	out.WriteString("// Generated by ARKHE Parser — C++ Target\n")
	out.WriteString("#include <iostream>\n\n")

	for _, node := range graph.Nodes {
		switch node.Type {
		case LFIRType:
			tsType, _ := node.Attributes["tree_sitter_type"].(string)
			// Emitir declaração forward ou definição
			if strings.Contains(tsType, "class") {
				out.WriteString(fmt.Sprintf("class %s {\npublic:\n", node.Name))
				out.WriteString("};\n\n")
			} else {
				out.WriteString(fmt.Sprintf("struct %s {\n", node.Name))
				out.WriteString("};\n\n")
			}
		case LFIRFunction:
			out.WriteString(fmt.Sprintf("void %s() {\n", snakeCase(node.Name)))
			out.WriteString("    // TODO: Implement function\n")
			out.WriteString("}\n\n")
		}
	}
	return out.String(), nil
}

func snakeCase(s string) string {
	var result strings.Builder
	for i, r := range s {
		if i > 0 && r >= 'A' && r <= 'Z' {
			result.WriteByte('_')
		}
		result.WriteRune(r)
	}
	return strings.ToLower(result.String())
}



func (pp *PolymathParser) registerDataCenterLanguage() {
	dcFrontend, _ := NewDataCenterFrontend("main-cluster")
	pp.RegisterFrontend(dcFrontend)
}

func (pp *PolymathParser) registerAdditionalLanguages() {
	pp.registerDataCenterLanguage()


	// Frontends
	csFrontend, _ := NewCSharpFrontend()
	pp.RegisterFrontend(csFrontend)
	cppFrontend, _ := NewCppFrontend()
	pp.RegisterFrontend(cppFrontend)

	// Backends
	pp.RegisterBackend(NewCSharpBackend())
	pp.RegisterBackend(NewCppBackend())
}
