package frontends

import (
	"encoding/json"
	"fmt"
	"math"
	"strings"
	"time"

	"arkhe/parser/lfir"
)

// GitHubFrontend implementa parsing de dados sociais do GitHub para LFIR
type GitHubFrontend struct {
	repoOwner    string
	repoName     string
	parserConfig GitHubParserConfig
}

// GitHubParserConfig contém configuração para parsing de GitHub
type GitHubParserConfig struct {
	IncludeIssues       bool
	IncludePullRequests bool
	IncludeActions      bool
	IncludeReactions    bool
	IncludeProjects     bool
	SentimentAnalysis   bool // Habilitar análise de sentimento em comentários
	CoherenceMapping    bool // Mapear eventos sociais para gradientes de coerência
	MaxItemsPerType     int  // Limite de itens por tipo para evitar overload
}

// NewGitHubFrontend cria novo frontend para parsing de GitHub
func NewGitHubFrontend(owner, name string, config GitHubParserConfig) (*GitHubFrontend, error) {
	return &GitHubFrontend{
		repoOwner:    owner,
		repoName:     name,
		parserConfig: config,
	}, nil
}

func (f *GitHubFrontend) GetLanguage() string { return "github" }
func (f *GitHubFrontend) GetExtensions() []string {
	return []string{".gh", ".github", ".ghdata", ".ghwebhook"}
}

// Parse processa JSON da API GitHub ou webhook e gera LFIRGraph
func (f *GitHubFrontend) Parse(source []byte) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	repoID := fmt.Sprintf("github/%s/%s", f.repoOwner, f.repoName)
	module := lfir.NewLFIRNode(lfir.LFIRModule, repoID, "github")
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)

	// Detectar tipo de payload GitHub
	payloadType := detectGitHubPayloadType(source)

	switch payloadType {
	case "repository":
		return f.parseRepositoryPayload(source, graph, module.ID)
	case "issues", "issue_comment":
		return f.parseIssuesPayload(source, graph, module.ID)
	case "pull_request", "pull_request_review":
		return f.parsePullRequestsPayload(source, graph, module.ID)
	case "workflow_run", "check_run":
		return f.parseActionsPayload(source, graph, module.ID)
	case "push", "release", "star", "fork":
		return f.parseActivityPayload(source, graph, module.ID, payloadType)
	default:
		// Tentar parse genérico como array ou objeto
		return f.parseGenericPayload(source, graph, module.ID)
	}
}

// detectGitHubPayloadType identifica tipo de payload GitHub baseado em campos
func detectGitHubPayloadType(source []byte) string {
	var obj map[string]interface{}
	if err := json.Unmarshal(source, &obj); err != nil {
		return "unknown"
	}

	// Verificar campos distintivos de tipos de payload
	if _, ok := obj["repository"]; ok {
		if _, ok := obj["issue"]; ok {
			return "issues"
		}
		if _, ok := obj["pull_request"]; ok {
			return "pull_request"
		}
		if _, ok := obj["workflow"]; ok {
			return "workflow_run"
		}
		return "repository"
	}
	if _, ok := obj["action"]; ok {
		switch obj["action"] {
		case "opened", "closed", "reopened":
			if _, ok := obj["pull_request"]; ok {
				return "pull_request"
			}
			return "issues"
		case "completed":
			return "workflow_run"
		case "created", "edited", "deleted":
			if _, ok := obj["comment"]; ok {
				return "issue_comment"
			}
			return "pull_request_review"
		}
	}
	if _, ok := obj["commits"]; ok {
		return "push"
	}
	if _, ok := obj["starred_at"]; ok {
		return "star"
	}
	return "unknown"
}

// parseRepositoryPayload processa payload de repositório
func (f *GitHubFrontend) parseRepositoryPayload(source []byte, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	var repo map[string]interface{}
	if err := json.Unmarshal(source, &repo); err != nil {
		return nil, err
	}

	node := lfir.NewLFIRNode(lfir.LFIRModule, fmt.Sprintf("repo/%v", repo["full_name"]), "github")
	node.Attributes["type"] = "repository"
	node.Attributes["description"] = getStringFromMap(repo, "description")
	node.Attributes["homepage"] = getStringFromMap(repo, "homepage")
	node.Attributes["language"] = getStringFromMap(repo, "language")
	node.Attributes["topics"] = getStringSlice(repo, "topics")

	// Métricas de engajamento social
	node.Attributes["stargazers_count"] = getIntFromMap(repo, "stargazers_count")
	node.Attributes["watchers_count"] = getIntFromMap(repo, "watchers_count")
	node.Attributes["forks_count"] = getIntFromMap(repo, "forks_count")
	node.Attributes["open_issues_count"] = getIntFromMap(repo, "open_issues_count")
	node.Attributes["subscribers_count"] = getIntFromMap(repo, "subscribers_count")

	// Metadados temporais
	node.Attributes["created_at"] = getStringFromMap(repo, "created_at")
	node.Attributes["updated_at"] = getStringFromMap(repo, "updated_at")
	node.Attributes["pushed_at"] = getStringFromMap(repo, "pushed_at")

	// Saúde do repositório (calculado)
	healthScore := computeRepositoryHealth(repo)
	node.Attributes["health_score"] = healthScore
	node.Attributes["parsed_at"] = time.Now().Unix()

	graph.AddNode(node)
	graph.Link(parentID, node.ID)

	return graph, nil
}

// parseIssuesPayload processa payload de issues ou comentários
func (f *GitHubFrontend) parseIssuesPayload(source []byte, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	// Tentar array primeiro
	var items []map[string]interface{}
	if err := json.Unmarshal(source, &items); err == nil {
		for _, item := range items {
			f.parseIssueItem(item, graph, parentID)
		}
		return graph, nil
	}

	// Tentar objeto único
	var item map[string]interface{}
	if err := json.Unmarshal(source, &item); err != nil {
		return nil, err
	}
	f.parseIssueItem(item, graph, parentID)
	return graph, nil
}

// parseIssueItem processa item individual de issue ou comentário
func (f *GitHubFrontend) parseIssueItem(item map[string]interface{}, graph *lfir.LFIRGraph, parentID string) {
	// Detectar se é issue ou comentário
	if _, isComment := item["issue_url"]; isComment {
		f.parseComment(item, graph, parentID)
		return
	}

	// É uma issue
	issueNum := getIntFromMap(item, "number")
	id := fmt.Sprintf("issue/%d", issueNum)
	node := lfir.NewLFIRNode(lfir.LFIROperation, id, "github")

	node.Attributes["type"] = "issue"
	node.Attributes["title"] = getStringFromMap(item, "title")
	node.Attributes["state"] = getStringFromMap(item, "state") // open/closed
	node.Attributes["locked"] = getBool(item, "locked")
	node.Attributes["created_at"] = getStringFromMap(item, "created_at")
	node.Attributes["updated_at"] = getStringFromMap(item, "updated_at")
	node.Attributes["closed_at"] = getStringFromMap(item, "closed_at")

	// Autor e atribuição
	if user, ok := item["user"].(map[string]interface{}); ok {
		node.Attributes["author"] = getStringFromMap(user, "login")
		node.Attributes["author_type"] = getStringFromMap(user, "type") // User/Org/Bot
	}
	if assignee, ok := item["assignee"].(map[string]interface{}); ok {
		node.Attributes["assignee"] = getStringFromMap(assignee, "login")
	}

	// Labels como tags semânticas
	if labels, ok := item["labels"].([]interface{}); ok {
		var labelNames, labelColors []string
		for _, l := range labels {
			if label, ok := l.(map[string]interface{}); ok {
				labelNames = append(labelNames, getStringFromMap(label, "name"))
				labelColors = append(labelColors, getStringFromMap(label, "color"))
			}
		}
		node.Attributes["labels"] = strings.Join(labelNames, ",")
		node.Attributes["label_colors"] = strings.Join(labelColors, ",")

		// Calcular peso de coerência baseado em labels
		if f.parserConfig.CoherenceMapping {
			node.Attributes["coherence_weight"] = computeLabelCoherenceWeight(labelNames)
		}
	}

	// Engajamento: comentários, reações
	node.Attributes["comments_count"] = getIntFromMap(item, "comments")
	if reactions, ok := item["reactions"].(map[string]interface{}); ok {
		node.Attributes["reactions_total"] = getIntFromMap(reactions, "total_count")
		node.Attributes["reactions_+1"] = getIntFromMap(reactions, "+1")
		node.Attributes["reactions_-1"] = getIntFromMap(reactions, "-1")
		node.Attributes["reactions_laugh"] = getIntFromMap(reactions, "laugh")
		node.Attributes["reactions_heart"] = getIntFromMap(reactions, "heart")
	}

	// Análise de sentimento se habilitado
	if f.parserConfig.SentimentAnalysis {
		sentiment := analyzeIssueSentiment(getStringFromMap(item, "title"), getStringFromMap(item, "body"))
		node.Attributes["sentiment_score"] = sentiment.Score
		node.Attributes["sentiment_label"] = sentiment.Label
	}

	// Cálculo de delta de coerência se habilitado
	if f.parserConfig.CoherenceMapping {
		delta := computeIssueCoherenceDelta(item, node.Attributes)
		node.Attributes["coherence_delta"] = delta
		node.Attributes["coherence_sign"] = "positive"
		if delta < 0 {
			node.Attributes["coherence_sign"] = "negative"
		}
	}

	graph.AddNode(node)
	graph.Link(parentID, node.ID)
}

// parseComment processa comentário de issue ou PR
func (f *GitHubFrontend) parseComment(item map[string]interface{}, graph *lfir.LFIRGraph, parentID string) {
	id := fmt.Sprintf("comment/%d", getIntFromMap(item, "id"))
	node := lfir.NewLFIRNode(lfir.LFIRMetadata, id, "github")

	node.Attributes["type"] = "comment"
	node.Attributes["body"] = getStringFromMap(item, "body")
	node.Attributes["created_at"] = getStringFromMap(item, "created_at")
	node.Attributes["updated_at"] = getStringFromMap(item, "updated_at")

	if user, ok := item["user"].(map[string]interface{}); ok {
		node.Attributes["author"] = getStringFromMap(user, "login")
	}

	// Reações ao comentário
	if reactions, ok := item["reactions"].(map[string]interface{}); ok {
		node.Attributes["reactions_total"] = getIntFromMap(reactions, "total_count")
	}

	// Sentimento do comentário se habilitado
	if f.parserConfig.SentimentAnalysis {
		sentiment := analyzeTextSentiment(getStringFromMap(item, "body"))
		node.Attributes["sentiment_score"] = sentiment.Score
		node.Attributes["sentiment_label"] = sentiment.Label
	}

	graph.AddNode(node)
	graph.Link(parentID, node.ID)
}

// parsePullRequestsPayload processa payload de PRs ou reviews
func (f *GitHubFrontend) parsePullRequestsPayload(source []byte, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	var items []map[string]interface{}
	if err := json.Unmarshal(source, &items); err == nil {
		for _, item := range items {
			f.parsePRItem(item, graph, parentID)
		}
		return graph, nil
	}

	var item map[string]interface{}
	if err := json.Unmarshal(source, &item); err != nil {
		return nil, err
	}
	f.parsePRItem(item, graph, parentID)
	return graph, nil
}

// parsePRItem processa item individual de PR ou review
func (f *GitHubFrontend) parsePRItem(item map[string]interface{}, graph *lfir.LFIRGraph, parentID string) {
	// Detectar se é PR ou review
	if _, isReview := item["pull_request_url"]; isReview {
		f.parsePRReview(item, graph, parentID)
		return
	}

	// É um pull request
	prNum := getIntFromMap(item, "number")
	id := fmt.Sprintf("pr/%d", prNum)
	node := lfir.NewLFIRNode(lfir.LFIROperation, id, "github")

	node.Attributes["type"] = "pull_request"
	node.Attributes["title"] = getStringFromMap(item, "title")
	node.Attributes["state"] = getStringFromMap(item, "state") // open/closed/merged
	node.Attributes["draft"] = getBool(item, "draft")
	node.Attributes["created_at"] = getStringFromMap(item, "created_at")
	node.Attributes["updated_at"] = getStringFromMap(item, "updated_at")
	node.Attributes["merged_at"] = getStringFromMap(item, "merged_at")
	node.Attributes["closed_at"] = getStringFromMap(item, "closed_at")

	// Branches
	node.Attributes["head_branch"] = getStringFromMap(item, "head", "ref")
	node.Attributes["base_branch"] = getStringFromMap(item, "base", "ref")

	// Autor e revisores
	if user, ok := item["user"].(map[string]interface{}); ok {
		node.Attributes["author"] = getStringFromMap(user, "login")
	}
	if requestedReviewers, ok := item["requested_reviewers"].([]interface{}); ok {
		var reviewers []string
		for _, r := range requestedReviewers {
			if reviewer, ok := r.(map[string]interface{}); ok {
				reviewers = append(reviewers, getStringFromMap(reviewer, "login"))
			}
		}
		node.Attributes["requested_reviewers"] = strings.Join(reviewers, ",")
	}

	// Métricas de mudança de código
	node.Attributes["additions"] = getIntFromMap(item, "additions")
	node.Attributes["deletions"] = getIntFromMap(item, "deletions")
	node.Attributes["changed_files"] = getIntFromMap(item, "changed_files")
	node.Attributes["commits_count"] = getIntFromMap(item, "commits")

	// Status de revisão e merge
	node.Attributes["reviews_count"] = getIntFromMap(item, "reviews", "total")
	node.Attributes["approved_reviews"] = getIntFromMap(item, "reviews", "approved")
	node.Attributes["changes_requested"] = getIntFromMap(item, "reviews", "changes_requested")
	node.Attributes["mergeable"] = getBool(item, "mergeable")
	node.Attributes["merged"] = getBool(item, "merged")

	// Cálculo de consenso de PR se habilitado
	if f.parserConfig.CoherenceMapping {
		consensus := computePRConsensus(item)
		node.Attributes["consensus_score"] = consensus.Score
		node.Attributes["consensus_status"] = consensus.Status
		node.Attributes["coherence_delta"] = consensus.CoherenceDelta
	}

	graph.AddNode(node)
	graph.Link(parentID, node.ID)
}

// parsePRReview processa review de pull request
func (f *GitHubFrontend) parsePRReview(item map[string]interface{}, graph *lfir.LFIRGraph, parentID string) {
	id := fmt.Sprintf("review/%d", getIntFromMap(item, "id"))
	node := lfir.NewLFIRNode(lfir.LFIRMetadata, id, "github")

	node.Attributes["type"] = "pull_request_review"
	node.Attributes["state"] = getStringFromMap(item, "state") // APPROVED/CHANGES_REQUESTED/COMMENTED
	node.Attributes["body"] = getStringFromMap(item, "body")
	node.Attributes["submitted_at"] = getStringFromMap(item, "submitted_at")

	if user, ok := item["user"].(map[string]interface{}); ok {
		node.Attributes["reviewer"] = getStringFromMap(user, "login")
	}

	// Sentimento do review se habilitado
	if f.parserConfig.SentimentAnalysis {
		sentiment := analyzeTextSentiment(getStringFromMap(item, "body"))
		node.Attributes["sentiment_score"] = sentiment.Score
		node.Attributes["sentiment_label"] = sentiment.Label
	}

	graph.AddNode(node)
	graph.Link(parentID, node.ID)
}

// parseActionsPayload processa payload de GitHub Actions/workflows
func (f *GitHubFrontend) parseActionsPayload(source []byte, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	var item map[string]interface{}
	if err := json.Unmarshal(source, &item); err != nil {
		return nil, err
	}

	id := fmt.Sprintf("workflow/%d", getIntFromMap(item, "run_id"))
	node := lfir.NewLFIRNode(lfir.LFIROperation, id, "github")

	node.Attributes["type"] = "workflow_run"
	node.Attributes["name"] = getStringFromMap(item, "workflow", "name")
	node.Attributes["status"] = getStringFromMap(item, "status") // queued/in_progress/completed
	node.Attributes["conclusion"] = getStringFromMap(item, "conclusion") // success/failure/cancelled
	node.Attributes["event"] = getStringFromMap(item, "event") // push/pull_request/schedule
	node.Attributes["created_at"] = getStringFromMap(item, "created_at")
	node.Attributes["updated_at"] = getStringFromMap(item, "updated_at")

	// Duração e timing
	if started, err := time.Parse(time.RFC3339, getStringFromMap(item, "run_started_at")); err == nil {
		if completed, err := time.Parse(time.RFC3339, getStringFromMap(item, "updated_at")); err == nil {
			duration := completed.Sub(started).Milliseconds()
			node.Attributes["duration_ms"] = duration
		}
	}

	// Trigger e contexto
	node.Attributes["trigger_actor"] = getStringFromMap(item, "actor", "login")
	node.Attributes["head_branch"] = getStringFromMap(item, "head_branch")
	node.Attributes["head_sha"] = getStringFromMap(item, "head_sha")

	// Coerência operacional: workflows bem-sucedidos contribuem positivamente
	if f.parserConfig.CoherenceMapping {
		delta := computeWorkflowCoherenceDelta(item)
		node.Attributes["coherence_delta"] = delta
		node.Attributes["coherence_sign"] = "positive"
		if delta < 0 {
			node.Attributes["coherence_sign"] = "negative"
		}
	}

	graph.AddNode(node)
	graph.Link(parentID, node.ID)
	return graph, nil
}

// parseActivityPayload processa eventos de atividade (push, star, fork, release)
func (f *GitHubFrontend) parseActivityPayload(source []byte, graph *lfir.LFIRGraph, parentID string, activityType string) (*lfir.LFIRGraph, error) {
	var item map[string]interface{}
	if err := json.Unmarshal(source, &item); err != nil {
		return nil, err
	}

	id := fmt.Sprintf("%s/%s", activityType, getStringFromMap(item, "action", "event"))
	node := lfir.NewLFIRNode(lfir.LFIRMetadata, id, "github")

	node.Attributes["type"] = activityType
	node.Attributes["action"] = getStringFromMap(item, "action")
	node.Attributes["timestamp"] = getStringFromMap(item, "created_at", "published_at", "starred_at")

	if sender, ok := item["sender"].(map[string]interface{}); ok {
		node.Attributes["actor"] = getStringFromMap(sender, "login")
		node.Attributes["actor_type"] = getStringFromMap(sender, "type")
	}

	// Contribuição para campo de atenção social
	if f.parserConfig.CoherenceMapping {
		attentionDelta := computeAttentionDelta(activityType, item)
		node.Attributes["attention_delta"] = attentionDelta
	}

	graph.AddNode(node)
	graph.Link(parentID, node.ID)
	return graph, nil
}

// parseGenericPayload tenta parse genérico para payloads não identificados
func (f *GitHubFrontend) parseGenericPayload(source []byte, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	// Tentar array
	var arr []map[string]interface{}
	if err := json.Unmarshal(source, &arr); err == nil {
		for _, item := range arr {
			f.parseItemGeneric(item, graph, parentID)
		}
		return graph, nil
	}

	// Tentar objeto
	var obj map[string]interface{}
	if err := json.Unmarshal(source, &obj); err != nil {
		return nil, fmt.Errorf("unrecognized GitHub JSON format")
	}
	f.parseItemGeneric(obj, graph, parentID)
	return graph, nil
}

// parseItemGeneric processa item genérico do GitHub
func (f *GitHubFrontend) parseItemGeneric(item map[string]interface{}, graph *lfir.LFIRGraph, parentID string) {
	// Heurísticas simples baseadas em campos presentes
	if _, ok := item["html_url"]; ok {
		if strings.Contains(getStringFromMap(item, "html_url"), "/pull/") {
			f.parsePRItem(item, graph, parentID)
			return
		}
		if strings.Contains(getStringFromMap(item, "html_url"), "/issues/") {
			f.parseIssueItem(item, graph, parentID)
			return
		}
	}
	if _, ok := item["full_name"]; ok {
		f.parseRepositoryPayload(jsonMustMarshal(item), graph, parentID)
		return
	}
	// Fallback: nó genérico com todos os campos
	node := lfir.NewLFIRNode(lfir.LFIRMetadata, fmt.Sprintf("generic/%s", getStringFromMap(item, "id", "unknown")), "github")
	for k, v := range item {
		if k != "node_id" { // Evitar duplicação de ID
			node.Attributes[k] = v
		}
	}
	graph.AddNode(node)
	graph.Link(parentID, node.ID)
}

// Helper functions para extração segura de campos JSON
func getStringFromMap(obj map[string]interface{}, keys ...string) string {
	var current interface{} = obj
	for i, key := range keys {
		if m, ok := current.(map[string]interface{}); ok {
			current = m[key]
			if i == len(keys)-1 {
				if s, ok := current.(string); ok {
					return s
				}
				return ""
			}
		} else {
			return ""
		}
	}
	return ""
}

func getIntFromMap(obj map[string]interface{}, keys ...string) int {
	var current interface{} = obj
	for i, key := range keys {
		if m, ok := current.(map[string]interface{}); ok {
			current = m[key]
			if i == len(keys)-1 {
				switch v := current.(type) {
				case float64:
					return int(v)
				case int:
					return v
				}
				return 0
			}
		} else {
			return 0
		}
	}
	return 0
}

func getBool(obj map[string]interface{}, keys ...string) bool {
	var current interface{} = obj
	for i, key := range keys {
		if m, ok := current.(map[string]interface{}); ok {
			current = m[key]
			if i == len(keys)-1 {
				if b, ok := current.(bool); ok {
					return b
				}
				return false
			}
		} else {
			return false
		}
	}
	return false
}

func getStringSlice(obj map[string]interface{}, key string) []string {
	if arr, ok := obj[key].([]interface{}); ok {
		var result []string
		for _, v := range arr {
			if s, ok := v.(string); ok {
				result = append(result, s)
			}
		}
		return result
	}
	return nil
}

func jsonMustMarshal(v interface{}) []byte {
	data, _ := json.Marshal(v)
	return data
}

// Funções de cálculo de métricas de coerência social
func computeRepositoryHealth(repo map[string]interface{}) float64 {
	// Heurística simplificada de saúde do repositório
	stars := float64(getIntFromMap(repo, "stargazers_count"))
	forks := float64(getIntFromMap(repo, "forks_count"))
	issues := float64(getIntFromMap(repo, "open_issues_count"))
	updated := getStringFromMap(repo, "updated_at")

	// Score base em engajamento
	engagement := math.Log1p(stars) + 0.5*math.Log1p(forks)

	// Penalidade por issues abertas não resolvidas
	issuePenalty := math.Min(1.0, issues/100.0)

	// Bonus por atividade recente
	activityBonus := 0.0
	if updated != "" {
		if t, err := time.Parse(time.RFC3339, updated); err == nil {
			daysSinceUpdate := time.Since(t).Hours() / 24
			if daysSinceUpdate < 30 {
				activityBonus = 0.2
			} else if daysSinceUpdate < 90 {
				activityBonus = 0.1
			}
		}
	}

	health := engagement*(1-issuePenalty) + activityBonus
	return math.Max(0, math.Min(1, health/10)) // Normalizar para [0, 1]
}

func computeLabelCoherenceWeight(labels []string) float64 {
	// Mapear labels para pesos de coerência
	weights := map[string]float64{
		"bug": -0.05, "critical": -0.10, "security": -0.08,
		"enhancement": 0.03, "feature": 0.02, "documentation": 0.01,
		"good first issue": 0.02, "help wanted": 0.01,
	}

	total := 0.0
	for _, label := range labels {
		if w, ok := weights[strings.ToLower(label)]; ok {
			total += w
		}
	}
	return total
}

type SentimentResult struct {
	Score float64 // [-1, 1]
	Label string  // positive/negative/neutral
}

func analyzeIssueSentiment(title, body string) SentimentResult {
	// Análise de sentimento simplificada por palavras-chave
	text := strings.ToLower(title + " " + body)

	positiveWords := []string{"fix", "resolve", "improve", "add", "enhance", "thanks", "great", "awesome"}
	negativeWords := []string{"bug", "error", "fail", "crash", "broken", "issue", "problem", "urgent"}

	posCount := countWords(text, positiveWords)
	negCount := countWords(text, negativeWords)

	if posCount > negCount+1 {
		return SentimentResult{Score: 0.5, Label: "positive"}
	} else if negCount > posCount+1 {
		return SentimentResult{Score: -0.5, Label: "negative"}
	}
	return SentimentResult{Score: 0.0, Label: "neutral"}
}

func analyzeTextSentiment(text string) SentimentResult {
	return analyzeIssueSentiment(text, "")
}

func countWords(text string, words []string) int {
	count := 0
	for _, word := range words {
		if strings.Contains(text, word) {
			count++
		}
	}
	return count
}

func computeIssueCoherenceDelta(item map[string]interface{}, attrs map[string]interface{}) float64 {
	delta := 0.0

	// Peso base por label
	if labels, ok := attrs["labels"].(string); ok && labels != "" {
		for _, label := range strings.Split(labels, ",") {
			delta += computeLabelCoherenceWeight([]string{strings.TrimSpace(label)})
		}
	}

	// Bonus por resolução rápida
	if state, ok := attrs["state"].(string); ok && state == "closed" {
		if createdAt, err := time.Parse(time.RFC3339, attrs["created_at"].(string)); err == nil {
			if closedAt, err := time.Parse(time.RFC3339, attrs["closed_at"].(string)); err == nil {
				resolveHours := closedAt.Sub(createdAt).Hours()
				if resolveHours < 24 {
					delta += 0.05 // Resolução rápida = positivo
				} else if resolveHours > 168 { // > 1 semana
					delta -= 0.02 // Demora excessiva = negativo
				}
			}
		}
	}

	// Penalidade por issue aberta há muito tempo
	if state, ok := attrs["state"].(string); ok && state == "open" {
		if createdAt, err := time.Parse(time.RFC3339, attrs["created_at"].(string)); err == nil {
			openDays := time.Since(createdAt).Hours() / 24
			if openDays > 90 {
				delta -= 0.03 // Issue negligenciada
			}
		}
	}

	// Bonus por engajamento saudável
	if comments, ok := attrs["comments_count"].(int); ok {
		if comments > 0 && comments < 50 {
			delta += 0.01 // Discussão produtiva
		} else if comments > 200 {
			delta -= 0.01 // Discussão excessiva pode indicar conflito
		}
	}

	return delta
}

type PRConsensusResult struct {
	Score           float64 // [0, 1]
	Status          string  // consensus_reached/needs_review/conflicted
	CoherenceDelta  float64
}

func computePRConsensus(item map[string]interface{}) PRConsensusResult {
	result := PRConsensusResult{Score: 0.5, Status: "needs_review"}

	// Contar reviews aprovados vs. mudanças solicitadas
	approved := getIntFromMap(item, "reviews", "approved")
	requested := getIntFromMap(item, "reviews", "changes_requested")
	total := approved + requested

	if total > 0 {
		result.Score = float64(approved) / float64(total)
		if result.Score >= 0.67 {
			result.Status = "consensus_reached"
		} else if result.Score <= 0.33 {
			result.Status = "conflicted"
		}
	}

	// Delta de coerência baseado em consenso e merge
	if merged, ok := item["merged"].(bool); ok && merged {
		result.CoherenceDelta = 0.05 * result.Score // PR mergeado com consenso = positivo
	} else if result.Status == "consensus_reached" {
		result.CoherenceDelta = 0.02 // Consenso sem merge ainda = levemente positivo
	} else if result.Status == "conflicted" {
		result.CoherenceDelta = -0.02 // Conflito = levemente negativo
	}

	return result
}

func computeWorkflowCoherenceDelta(item map[string]interface{}) float64 {
	status := getStringFromMap(item, "status")
	conclusion := getStringFromMap(item, "conclusion")

	// Workflows bem-sucedidos contribuem positivamente
	if status == "completed" && conclusion == "success" {
		return 0.02
	} else if status == "completed" && conclusion == "failure" {
		return -0.01 // Falha leve (pode ser esperado em CI)
	} else if status == "completed" && conclusion == "cancelled" {
		return -0.03 // Cancelamento pode indicar problema
	}
	return 0.0 // Em andamento = neutro
}

func computeAttentionDelta(activityType string, item map[string]interface{}) float64 {
	// Contribuição para campo de atenção social por tipo de atividade
	switch activityType {
	case "star":
		return 0.001 // Cada star = pequeno pulso de atenção
	case "fork":
		return 0.005 // Fork = interesse em contribuir
	case "push":
		return 0.002 // Atividade de desenvolvimento
	case "release":
		return 0.01 // Release = marco importante
	default:
		return 0.0
	}
}
