package frontends

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"time"

	"arkhe/parser/lfir"
)

// GitWorkflowFrontend implementa parsing de histórico Git para LFIR
type GitWorkflowFrontend struct {
	repoPath     string
	parserConfig GitParserConfig
}

// GitParserConfig contém configuração para parsing de Git
type GitParserConfig struct {
	IncludeDiffs     bool
	IncludeBranches  bool
	IncludeTags      bool
	IncludeReflog    bool
	MaxCommits       int
	SemanticAnalysis bool // Habilitar análise semântica de mensagens de commit
	CoherenceMapping bool // Mapear commits para gradientes de coerência
}

// NewGitWorkflowFrontend cria novo frontend para parsing de Git
func NewGitWorkflowFrontend(repoPath string, config GitParserConfig) *GitWorkflowFrontend {
	return &GitWorkflowFrontend{
		repoPath:     repoPath,
		parserConfig: config,
	}
}

func (f *GitWorkflowFrontend) GetLanguage() string { return "git" }
func (f *GitWorkflowFrontend) GetExtensions() []string {
	return []string{".gitlog", ".git", ".gitgraph", ".gitreflog"}
}

// Parse analisa saída de comandos Git e gera LFIRGraph
func (f *GitWorkflowFrontend) Parse(source []byte) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	repoID := strings.TrimPrefix(f.repoPath, "/")
	module := lfir.NewLFIRNode(lfir.LFIRModule, repoID, "git")
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)

	content := string(source)
	lines := strings.Split(content, "\n")

	// Mapear hashes para IDs de nós e metadados
	commitNodes := make(map[string]*lfir.LFIRNode)
	branchHeads := make(map[string]string) // branch -> latest commit hash

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Parsing de commit: formato "hash|author|email|timestamp|message"
		if strings.Count(line, "|") >= 4 {
			if err := f.parseCommit(line, graph, module.ID, commitNodes); err != nil {
				continue
			}
		}

		// Parsing de branch: "branch: main" ou "branch: feature/xyz"
		if f.parserConfig.IncludeBranches && strings.HasPrefix(line, "branch:") {
			if err := f.parseBranch(line, graph, module.ID, branchHeads); err != nil {
				continue
			}
		}

		// Parsing de tag: "tag: v1.0.0"
		if f.parserConfig.IncludeTags && strings.HasPrefix(line, "tag:") {
			if err := f.parseTag(line, graph, module.ID); err != nil {
				continue
			}
		}

		// Parsing de diff stats: "+123 -45" em linhas de commit
		if f.parserConfig.IncludeDiffs && (strings.Contains(line, "+") || strings.Contains(line, "-")) {
			if err := f.parseDiffStats(line, graph, commitNodes); err != nil {
				continue
			}
		}
	}

	// Construir grafo de parentesco entre commits (ordem topológica)
	if err := f.buildCommitGraph(graph, commitNodes, lines); err != nil {
		// Logar erro mas não falhar o parsing
	}

	// Conectar branches aos seus commits head
	for branchName, commitHash := range branchHeads {
		if commitNodeID, ok := commitNodes[commitHash[:8]]; ok {
			if branchNode, exists := graph.FindNodeByAttribute("name", branchName); exists {
				graph.Link(branchNode.ID, commitNodeID.ID)
			}
		}
	}

	return graph, nil
}

// parseCommit extrai informações de commit de linha formatada
func (f *GitWorkflowFrontend) parseCommit(
	line string,
	graph *lfir.LFIRGraph,
	moduleID string,
	commitNodes map[string]*lfir.LFIRNode,
) error {
	parts := strings.SplitN(line, "|", 5)
	if len(parts) < 4 {
		return fmt.Errorf("insufficient fields in commit line")
	}

	hash := strings.TrimSpace(parts[0])
	author := strings.TrimSpace(parts[1])
	email := strings.TrimSpace(parts[2])
	timestampStr := strings.TrimSpace(parts[3])
	message := ""
	if len(parts) == 5 {
		message = strings.TrimSpace(parts[4])
	}

	// Criar nó de commit
	commitID := hash
	if len(hash) > 8 {
	    commitID = hash[:8] // Short hash para ID
    }
	commitNode := lfir.NewLFIRNode(lfir.LFIROperation, commitID, "git")
	commitNode.Attributes["full_hash"] = hash
	commitNode.Attributes["author"] = author
	commitNode.Attributes["author_email"] = email
	commitNode.Attributes["timestamp"] = timestampStr
	commitNode.Attributes["message"] = message
	commitNode.Attributes["type"] = "commit"

	// Análise semântica da mensagem se habilitado
	if f.parserConfig.SemanticAnalysis {
		semanticTags := extractSemanticTags(message)
		commitNode.Attributes["semantic_tags"] = semanticTags
		commitNode.Attributes["commit_type"] = classifyCommitType(message)
	}

	// Mapeamento para coerência se habilitado
	if f.parserConfig.CoherenceMapping {
		coherenceDelta := computeCommitCoherenceDelta(message, commitNode.Attributes)
		commitNode.Attributes["coherence_delta"] = coherenceDelta
		commitNode.Attributes["coherence_sign"] = "positive"
		if coherenceDelta < 0 {
			commitNode.Attributes["coherence_sign"] = "negative"
		}
	}

	graph.AddNode(commitNode)
	graph.Link(moduleID, commitNode.ID)
	commitNodes[commitID] = commitNode

	return nil
}

// parseBranch extrai informações de branch
func (f *GitWorkflowFrontend) parseBranch(
	line string,
	graph *lfir.LFIRGraph,
	moduleID string,
	branchHeads map[string]string,
) error {
	branchName := strings.TrimPrefix(line, "branch:")
	branchName = strings.TrimSpace(branchName)

	// Detectar se é branch atual
	isCurrent := strings.HasPrefix(branchName, "*")
	if isCurrent {
		branchName = strings.TrimSpace(strings.TrimPrefix(branchName, "*"))
	}

	branchNode := lfir.NewLFIRNode(lfir.LFIRType, branchName, "git")
	branchNode.Attributes["type"] = "branch"
	branchNode.Attributes["is_current"] = isCurrent
	branchNode.Attributes["created_at"] = time.Now().Unix() // Simplificado
	branchNode.Attributes["name"] = branchName

	graph.AddNode(branchNode)
	graph.Link(moduleID, branchNode.ID)

	return nil
}

// parseTag extrai informações de tag/release
func (f *GitWorkflowFrontend) parseTag(
	line string,
	graph *lfir.LFIRGraph,
	moduleID string,
) error {
	tagName := strings.TrimPrefix(line, "tag:")
	tagName = strings.TrimSpace(tagName)

	tagNode := lfir.NewLFIRNode(lfir.LFIRType, tagName, "git")
	tagNode.Attributes["type"] = "tag"
	tagNode.Attributes["release"] = isReleaseTag(tagName)
	tagNode.Attributes["semantic_version"] = parseSemanticVersion(tagName)

	graph.AddNode(tagNode)
	graph.Link(moduleID, tagNode.ID)

	return nil
}

// parseDiffStats extrai métricas de diff de linha de commit
func (f *GitWorkflowFrontend) parseDiffStats(
	line string,
	graph *lfir.LFIRGraph,
	commitNodes map[string]*lfir.LFIRNode,
) error {
	// Encontrar commit hash na linha (primeiros 8 caracteres alfanuméricos)
	hashMatch := regexp.MustCompile(`\b([a-f0-9]{8,40})\b`).FindString(line)
	if hashMatch == "" {
		return nil
	}
	commitID := hashMatch
	if len(hashMatch) > 8 {
	    commitID = hashMatch[:8]
    }

	commitNode, exists := commitNodes[commitID]
	if !exists {
		return nil
	}

	// Extrair estatísticas de adições/remoções
	added, removed := extractDiffStats(line)

	diffNode := lfir.NewLFIRNode(lfir.LFIRMetadata, commitID+"_diff", "git")
	diffNode.Attributes["lines_added"] = added
	diffNode.Attributes["lines_removed"] = removed
	diffNode.Attributes["net_change"] = added - removed
	diffNode.Attributes["churn"] = added + removed

	graph.AddNode(diffNode)
	graph.Link(commitNode.ID, diffNode.ID)

	return nil
}

// buildCommitGraph constrói arestas de parentesco entre commits
func (f *GitWorkflowFrontend) buildCommitGraph(
	graph *lfir.LFIRGraph,
	commitNodes map[string]*lfir.LFIRNode,
	lines []string,
) error {
	var prevCommitID string

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if !strings.Contains(line, "|") {
			continue
		}

		parts := strings.SplitN(line, "|", 2)
		if len(parts) < 1 {
			continue
		}

		hash := strings.TrimSpace(parts[0])
		commitID := hash
		if len(hash) > 8 {
		    commitID = hash[:8]
        }

		if node, ok := commitNodes[commitID]; ok {
			if prevCommitID != "" {
				// Criar aresta de parentesco (filho → pai)
				graph.Link(node.ID, prevCommitID)
			}
			prevCommitID = node.ID
		}
	}

	return nil
}

// Helper functions
func extractDiffStats(line string) (added, removed int) {
	// Procura padrões como "+123" ou "-45" em contexto de diff
	reAdded := regexp.MustCompile(`\+(\d+)\b`)
	reRemoved := regexp.MustCompile(`\-(\d+)\b`)

	for _, match := range reAdded.FindAllStringSubmatch(line, -1) {
		if len(match) > 1 {
			if val, err := strconv.Atoi(match[1]); err == nil {
				added += val
			}
		}
	}
	for _, match := range reRemoved.FindAllStringSubmatch(line, -1) {
		if len(match) > 1 {
			if val, err := strconv.Atoi(match[1]); err == nil {
				removed += val
			}
		}
	}
	return
}

func extractSemanticTags(message string) []string {
	// Extrair tags semânticas da mensagem de commit
	tags := []string{}
	messageLower := strings.ToLower(message)

	if strings.Contains(messageLower, "fix") || strings.Contains(messageLower, "bug") {
		tags = append(tags, "bugfix")
	}
	if strings.Contains(messageLower, "feat") || strings.Contains(messageLower, "feature") {
		tags = append(tags, "feature")
	}
	if strings.Contains(messageLower, "refactor") {
		tags = append(tags, "refactor")
	}
	if strings.Contains(messageLower, "test") {
		tags = append(tags, "testing")
	}
	if strings.Contains(messageLower, "docs") || strings.Contains(messageLower, "documentation") {
		tags = append(tags, "documentation")
	}
	if strings.Contains(messageLower, "perf") || strings.Contains(messageLower, "performance") {
		tags = append(tags, "performance")
	}
	if strings.Contains(messageLower, "security") {
		tags = append(tags, "security")
	}

	return tags
}

func classifyCommitType(message string) string {
	messageLower := strings.ToLower(message)
	if strings.HasPrefix(messageLower, "fix:") || strings.Contains(messageLower, "bugfix") {
		return "fix"
	}
	if strings.HasPrefix(messageLower, "feat:") || strings.Contains(messageLower, "feature") {
		return "feature"
	}
	if strings.HasPrefix(messageLower, "chore:") {
		return "chore"
	}
	if strings.HasPrefix(messageLower, "docs:") {
		return "docs"
	}
	if strings.HasPrefix(messageLower, "refactor:") {
		return "refactor"
	}
	if strings.HasPrefix(messageLower, "test:") {
		return "test"
	}
	return "other"
}

func isReleaseTag(tagName string) bool {
	// Verificar se tag segue padrão de release (ex: v1.0.0, 2.3.1)
	return regexp.MustCompile(`^v?\d+\.\d+\.\d+`).MatchString(tagName)
}

func parseSemanticVersion(tagName string) map[string]int {
	// Parsear versão semântica: major.minor.patch
	version := map[string]int{"major": 0, "minor": 0, "patch": 0}
	tagName = strings.TrimPrefix(tagName, "v")

	parts := strings.Split(tagName, ".")
	if len(parts) >= 1 {
		if major, err := strconv.Atoi(parts[0]); err == nil {
			version["major"] = major
		}
	}
	if len(parts) >= 2 {
		if minor, err := strconv.Atoi(parts[1]); err == nil {
			version["minor"] = minor
		}
	}
	if len(parts) >= 3 {
		if patch, err := strconv.Atoi(strings.Split(parts[2], "-")[0]); err == nil {
			version["patch"] = patch
		}
	}
	return version
}

func computeCommitCoherenceDelta(message string, attributes map[string]interface{}) float64 {
	// Calcular contribuição de coerência do commit baseado em heurísticas
	delta := 0.0

	// Tags semânticas positivas
	tags, ok := attributes["semantic_tags"].([]string)
	if ok {
		for _, tag := range tags {
			switch tag {
			case "bugfix", "security", "performance":
				delta += 0.05
			case "feature":
				delta += 0.02
			case "refactor":
				delta += 0.01
			case "documentation", "testing":
				delta += 0.005
			}
		}
	}

	// Penalizar commits com mensagens vagas
	if len(message) < 20 {
		delta -= 0.03
	}

	// Bonus para commits com review score alto (se disponível)
	if score, ok := attributes["review_score"].(float64); ok {
		delta += score * 0.02
	}

	return delta
}
