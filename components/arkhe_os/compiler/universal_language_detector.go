// arkhe_os/compiler/universal_language_detector.go
package compiler

import (
    "bufio"
    "os"
    "path/filepath"
    "regexp"
    "strings"
    "sync"
	"bufio"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
)

// DetectionStage enumera os estágios de detecção
type DetectionStage int

const (
    StageExtension DetectionStage = iota
    StageShebang
    StageKeywords
    StageStructure
    StageFallback
	StageExtension DetectionStage = iota
	StageShebang
	StageKeywords
	StageStructure
	StageFallback
)

// DetectionResult contém resultado da detecção com confiança
type DetectionResult struct {
    Language   string         `json:"language"`
    Confidence float64        `json:"confidence"`  // [0,1]
    Stage      DetectionStage `json:"stage"`       // Estágio que determinou
    Evidence   []string       `json:"evidence"`    // Evidências usadas
    Entry      *ExtensionEntry `json:"entry,omitempty"`
	Language   string          `json:"language"`
	Confidence float64         `json:"confidence"` // [0,1]
	Stage      DetectionStage  `json:"stage"`      // Estágio que determinou
	Evidence   []string        `json:"evidence"`   // Evidências usadas
	Entry      *ExtensionEntry `json:"entry,omitempty"`
}

// UniversalLanguageDetector implementa detecção em 3 estágios + fallback
type UniversalLanguageDetector struct {
    catalog *LanguageCatalog
    mu      sync.Mutex

    // Pesos para scoring bayesiano
    weights map[DetectionStage]float64

    // Padrões regex pré-compilados
    shebangRegex *regexp.Regexp
    keywordRegexes map[string][]*regexp.Regexp
	catalog *LanguageCatalog
	mu      sync.Mutex

	// Pesos para scoring bayesiano
	weights map[DetectionStage]float64

	// Padrões regex pré-compilados
	shebangRegex   *regexp.Regexp
	keywordRegexes map[string][]*regexp.Regexp
}

// NewUniversalLanguageDetector cria detector com catálogo
func NewUniversalLanguageDetector(catalog *LanguageCatalog) *UniversalLanguageDetector {
    d := &UniversalLanguageDetector{
        catalog: catalog,
        weights: map[DetectionStage]float64{
            StageExtension: 0.40,
            StageShebang:   0.30,
            StageKeywords:  0.20,
            StageStructure: 0.08,
            StageFallback:  0.02,
        },
        shebangRegex: regexp.MustCompile(`^#!\s*(?:/usr/bin/env\s+)?([^\s/]+)`),
        keywordRegexes: make(map[string][]*regexp.Regexp),
    }
    d.precompilePatterns()
    return d
}

func (d *UniversalLanguageDetector) precompilePatterns() {
    // Pré-compilar regex para keywords por linguagem
    for lang, entry := range d.catalog.byLanguage {
        if len(entry.Keywords) == 0 {
            continue
        }
        regexes := make([]*regexp.Regexp, 0, len(entry.Keywords))
        for _, kw := range entry.Keywords {
            // Escapar caracteres especiais e compilar
            escaped := regexp.QuoteMeta(strings.TrimSpace(kw))
            if re, err := regexp.Compile(escaped); err == nil {
                regexes = append(regexes, re)
            }
        }
        d.keywordRegexes[lang] = regexes
    }
	d := &UniversalLanguageDetector{
		catalog: catalog,
		weights: map[DetectionStage]float64{
			StageExtension: 0.40,
			StageShebang:   0.30,
			StageKeywords:  0.20,
			StageStructure: 0.08,
			StageFallback:  0.02,
		},
		shebangRegex:   regexp.MustCompile(`^#!\s*(?:/usr/bin/env\s+)?([^\s/]+)`),
		keywordRegexes: make(map[string][]*regexp.Regexp),
	}
	d.precompilePatterns()
	return d
}

func (d *UniversalLanguageDetector) precompilePatterns() {
	// Pré-compilar regex para keywords por linguagem
	for lang, entry := range d.catalog.byLanguage {
		if len(entry.Keywords) == 0 {
			continue
		}
		regexes := make([]*regexp.Regexp, 0, len(entry.Keywords))
		for _, kw := range entry.Keywords {
			// Escapar caracteres especiais e compilar
			escaped := regexp.QuoteMeta(strings.TrimSpace(kw))
			if re, err := regexp.Compile(escaped); err == nil {
				regexes = append(regexes, re)
			}
		}
		d.keywordRegexes[lang] = regexes
	}
}

// DetectLanguageFromFile executa detecção completa em arquivo
func (d *UniversalLanguageDetector) DetectLanguageFromFile(filePath string) DetectionResult {
    ext := filepath.Ext(filePath)
    filename := filepath.Base(filePath)

    // Estágio 1: Extensão + arquivo especial
    if result := d.detectByExtension(filePath, ext, filename); result.Confidence >= 0.85 {
        return result
    }

    // Estágio 2: Shebang
    if result := d.detectByShebang(filePath); result.Confidence >= 0.80 {
        return result
    }

    // Estágio 3: Palavras-chave
    if result := d.detectByKeywords(filePath); result.Confidence >= 0.60 {
        return result
    }

    // Estágio 4: Estrutura sintática (simplificado)
    if result := d.detectByStructure(filePath); result.Confidence >= 0.50 {
        return result
    }

    // Estágio 5: Fallback para texto genérico
    return DetectionResult{
        Language:   "text",
        Confidence: 0.10,
        Stage:      StageFallback,
        Evidence:   []string{"no_match"},
    }
}

func (d *UniversalLanguageDetector) detectByExtension(filePath, ext, filename string) DetectionResult {
    // Verificar arquivo especial primeiro
    if entry := d.catalog.LookupBySpecialFile(filename); entry != nil {
        return DetectionResult{
            Language:   entry.Language,
            Confidence: 0.95,
            Stage:      StageExtension,
            Evidence:   []string{"special_file:" + filename},
            Entry:      entry,
        }
    }

    // Verificar por extensão
    if entry := d.catalog.LookupByExtension(ext); entry != nil {
        return DetectionResult{
            Language:   entry.Language,
            Confidence: 0.90,
            Stage:      StageExtension,
            Evidence:   []string{"extension:" + ext},
            Entry:      entry,
        }
    }

    return DetectionResult{Confidence: 0.0}
}

func (d *UniversalLanguageDetector) detectByShebang(filePath string) DetectionResult {
    file, err := os.Open(filePath)
    if err != nil {
        return DetectionResult{Confidence: 0.0}
    }
    defer file.Close()

    reader := bufio.NewReader(file)
    firstLine, err := reader.ReadString('\n')
    if err != nil || !strings.HasPrefix(firstLine, "#!") {
        return DetectionResult{Confidence: 0.0}
    }

    // Extrair interpretador do shebang
    matches := d.shebangRegex.FindStringSubmatch(firstLine)
    if len(matches) < 2 {
        return DetectionResult{Confidence: 0.0}
    }

    interpreter := strings.ToLower(matches[1])

    // Buscar linguagem por shebang no catálogo
    for _, entry := range d.catalog.byLanguage {
        for _, sb := range entry.Shebang {
            if strings.Contains(interpreter, strings.ToLower(sb)) {
                return DetectionResult{
                    Language:   entry.Language,
                    Confidence: 0.95,
                    Stage:      StageShebang,
                    Evidence:   []string{"shebang:" + interpreter},
                    Entry:      entry,
                }
            }
        }
    }

    // Fallback: usar nome do interpretador como linguagem
    return DetectionResult{
        Language:   interpreter,
        Confidence: 0.70,
        Stage:      StageShebang,
        Evidence:   []string{"shebang_fallback:" + interpreter},
    }
}

func (d *UniversalLanguageDetector) detectByKeywords(filePath string) DetectionResult {
    content, err := os.ReadFile(filePath)
    if err != nil {
        return DetectionResult{Confidence: 0.0}
    }

    // Analisar primeiras 100 linhas para keywords
    lines := strings.Split(string(content), "\n")
    sampleSize := 100
    if len(lines) < sampleSize {
        sampleSize = len(lines)
    }
    sample := strings.Join(lines[:sampleSize], "\n")

    bestLang := ""
    bestScore := 0.0
    bestEvidence := []string{}

    for lang, regexes := range d.keywordRegexes {
        if len(regexes) == 0 {
            continue
        }

        score := 0.0
        evidence := []string{}

        for i, re := range regexes {
            if re.MatchString(sample) {
                score += 1.0 / float64(len(regexes))
                evidence = append(evidence, "kw:"+d.catalog.byLanguage[lang].Keywords[i])
            }
        }

        if score > bestScore && score >= 0.3 {
            bestScore = score
            bestLang = lang
            bestEvidence = evidence
        }
    }

    if bestLang != "" {
        return DetectionResult{
            Language:   bestLang,
            Confidence: bestScore * 0.9, // Penalizar levemente vs extensão/shebang
            Stage:      StageKeywords,
            Evidence:   bestEvidence,
            Entry:      d.catalog.byLanguage[bestLang],
        }
    }

    return DetectionResult{Confidence: 0.0}
}

func (d *UniversalLanguageDetector) detectByStructure(filePath string) DetectionResult {
    // Detecção estrutural simplificada: contar padrões de indentação, chaves, etc.
    content, err := os.ReadFile(filePath)
    if err != nil {
        return DetectionResult{Confidence: 0.0}
    }

    text := string(content)

    // Heurísticas estruturais por família
    scores := make(map[LanguageFamily]float64)

    // Indentação significativa (Python, YAML, etc.)
    if strings.Count(text, "\n    ") > strings.Count(text, "\n\t")*2 {
        scores[FamilyScripting] += 0.3
        scores[FamilyConfig] += 0.2
    }

    // Chaves para blocos (C-family, JS, etc.)
    if strings.Count(text, "{") > 10 && strings.Count(text, "}") > 10 {
        scores[FamilySystems] += 0.3
        scores[FamilyWeb] += 0.2
    }

    // Tags XML/HTML
    if strings.Count(text, "<") > 5 && strings.Count(text, ">") > 5 {
        if strings.Contains(text, "</") {
            scores[FamilyMarkup] += 0.4
        }
    }

    // Encontrar família com maior score
    bestFamily := LanguageFamily("")
    bestScore := 0.0
    for family, score := range scores {
        if score > bestScore {
            bestScore = score
            bestFamily = family
        }
    }

    if bestScore >= 0.3 && bestFamily != "" {
        // Retornar primeira linguagem da família
        langs := d.catalog.GetLanguagesByFamily(bestFamily)
        if len(langs) > 0 {
            entry := d.catalog.byLanguage[langs[0]]
            return DetectionResult{
                Language:   langs[0],
                Confidence: bestScore * 0.7,
                Stage:      StageStructure,
                Evidence:   []string{"structure:" + string(bestFamily)},
                Entry:      entry,
            }
        }
    }

    return DetectionResult{Confidence: 0.0}
	ext := filepath.Ext(filePath)
	filename := filepath.Base(filePath)

	// Estágio 1: Extensão + arquivo especial
	if result := d.detectByExtension(filePath, ext, filename); result.Confidence >= 0.85 {
		return result
	}

	// Estágio 2: Shebang
	if result := d.detectByShebang(filePath); result.Confidence >= 0.80 {
		return result
	}

	// Estágio 3: Palavras-chave
	if result := d.detectByKeywords(filePath); result.Confidence >= 0.60 {
		return result
	}

	// Estágio 4: Estrutura sintática (simplificado)
	if result := d.detectByStructure(filePath); result.Confidence >= 0.50 {
		return result
	}

	// Estágio 5: Fallback para texto genérico
	return DetectionResult{
		Language:   "text",
		Confidence: 0.10,
		Stage:      StageFallback,
		Evidence:   []string{"no_match"},
	}
}

func (d *UniversalLanguageDetector) detectByExtension(filePath, ext, filename string) DetectionResult {
	// Verificar arquivo especial primeiro
	if entry := d.catalog.LookupBySpecialFile(filename); entry != nil {
		return DetectionResult{
			Language:   entry.Language,
			Confidence: 0.95,
			Stage:      StageExtension,
			Evidence:   []string{"special_file:" + filename},
			Entry:      entry,
		}
	}

	// Verificar por extensão
	if entry := d.catalog.LookupByExtension(ext); entry != nil {
		return DetectionResult{
			Language:   entry.Language,
			Confidence: 0.90,
			Stage:      StageExtension,
			Evidence:   []string{"extension:" + ext},
			Entry:      entry,
		}
	}

	return DetectionResult{Confidence: 0.0}
}

func (d *UniversalLanguageDetector) detectByShebang(filePath string) DetectionResult {
	file, err := os.Open(filePath)
	if err != nil {
		return DetectionResult{Confidence: 0.0}
	}
	defer file.Close()

	reader := bufio.NewReader(file)
	firstLine, err := reader.ReadString('\n')
	if err != nil || !strings.HasPrefix(firstLine, "#!") {
		return DetectionResult{Confidence: 0.0}
	}

	// Extrair interpretador do shebang
	matches := d.shebangRegex.FindStringSubmatch(firstLine)
	if len(matches) < 2 {
		return DetectionResult{Confidence: 0.0}
	}

	interpreter := strings.ToLower(matches[1])

	// Buscar linguagem por shebang no catálogo
	for _, entry := range d.catalog.byLanguage {
		for _, sb := range entry.Shebang {
			if strings.Contains(interpreter, strings.ToLower(sb)) {
				return DetectionResult{
					Language:   entry.Language,
					Confidence: 0.95,
					Stage:      StageShebang,
					Evidence:   []string{"shebang:" + interpreter},
					Entry:      entry,
				}
			}
		}
	}

	// Fallback: usar nome do interpretador como linguagem
	return DetectionResult{
		Language:   interpreter,
		Confidence: 0.70,
		Stage:      StageShebang,
		Evidence:   []string{"shebang_fallback:" + interpreter},
	}
}

func (d *UniversalLanguageDetector) detectByKeywords(filePath string) DetectionResult {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return DetectionResult{Confidence: 0.0}
	}

	// Analisar primeiras 100 linhas para keywords
	lines := strings.Split(string(content), "\n")
	sampleSize := 100
	if len(lines) < sampleSize {
		sampleSize = len(lines)
	}
	sample := strings.Join(lines[:sampleSize], "\n")

	bestLang := ""
	bestScore := 0.0
	bestEvidence := []string{}

	for lang, regexes := range d.keywordRegexes {
		if len(regexes) == 0 {
			continue
		}

		score := 0.0
		evidence := []string{}

		for i, re := range regexes {
			if re.MatchString(sample) {
				score += 1.0 / float64(len(regexes))
				evidence = append(evidence, "kw:"+d.catalog.byLanguage[lang].Keywords[i])
			}
		}

		if score > bestScore && score >= 0.3 {
			bestScore = score
			bestLang = lang
			bestEvidence = evidence
		}
	}

	if bestLang != "" {
		return DetectionResult{
			Language:   bestLang,
			Confidence: bestScore * 0.9, // Penalizar levemente vs extensão/shebang
			Stage:      StageKeywords,
			Evidence:   bestEvidence,
			Entry:      d.catalog.byLanguage[bestLang],
		}
	}

	return DetectionResult{Confidence: 0.0}
}

func (d *UniversalLanguageDetector) detectByStructure(filePath string) DetectionResult {
	// Detecção estrutural simplificada: contar padrões de indentação, chaves, etc.
	content, err := os.ReadFile(filePath)
	if err != nil {
		return DetectionResult{Confidence: 0.0}
	}

	text := string(content)

	// Heurísticas estruturais por família
	scores := make(map[LanguageFamily]float64)

	// Indentação significativa (Python, YAML, etc.)
	if strings.Count(text, "\n    ") > strings.Count(text, "\n\t")*2 {
		scores[FamilyScripting] += 0.3
		scores[FamilyConfig] += 0.2
	}

	// Chaves para blocos (C-family, JS, etc.)
	if strings.Count(text, "{") > 10 && strings.Count(text, "}") > 10 {
		scores[FamilySystems] += 0.3
		scores[FamilyWeb] += 0.2
	}

	// Tags XML/HTML
	if strings.Count(text, "<") > 5 && strings.Count(text, ">") > 5 {
		if strings.Contains(text, "</") {
			scores[FamilyMarkup] += 0.4
		}
	}

	// Encontrar família com maior score
	bestFamily := LanguageFamily("")
	bestScore := 0.0
	for family, score := range scores {
		if score > bestScore {
			bestScore = score
			bestFamily = family
		}
	}

	if bestScore >= 0.3 && bestFamily != "" {
		// Retornar primeira linguagem da família
		langs := d.catalog.GetLanguagesByFamily(bestFamily)
		if len(langs) > 0 {
			entry := d.catalog.byLanguage[langs[0]]
			return DetectionResult{
				Language:   langs[0],
				Confidence: bestScore * 0.7,
				Stage:      StageStructure,
				Evidence:   []string{"structure:" + string(bestFamily)},
				Entry:      entry,
			}
		}
	}

	return DetectionResult{Confidence: 0.0}
}

// DetectLanguageByContent detecta linguagem diretamente de conteúdo (sem arquivo)
func (d *UniversalLanguageDetector) DetectLanguageByContent(content string) DetectionResult {
    // Implementação simplificada: pular extensão, ir direto para shebang/keywords
    if strings.HasPrefix(content, "#!") {
        // Extrair shebang da primeira linha
        lines := strings.SplitN(content, "\n", 2)
        firstLine := lines[0]
        matches := d.shebangRegex.FindStringSubmatch(firstLine)
        if len(matches) >= 2 {
            interpreter := strings.ToLower(matches[1])
            for _, entry := range d.catalog.byLanguage {
                for _, sb := range entry.Shebang {
                    if strings.Contains(interpreter, strings.ToLower(sb)) {
                        return DetectionResult{
                            Language:   entry.Language,
                            Confidence: 0.90,
                            Stage:      StageShebang,
                            Evidence:   []string{"shebang:" + interpreter},
                            Entry:      entry,
                        }
                    }
                }
            }
        }
    }

    // Detectar por keywords
    return d.detectByKeywordsContent(content)
}

func (d *UniversalLanguageDetector) detectByKeywordsContent(content string) DetectionResult {
    bestLang := ""
    bestScore := 0.0

    for lang, regexes := range d.keywordRegexes {
        score := 0.0
        for _, re := range regexes {
            if re.MatchString(content) {
                score += 1.0 / float64(len(regexes))
            }
        }
        if score > bestScore && score >= 0.3 {
            bestScore = score
            bestLang = lang
        }
    }

    if bestLang != "" {
        return DetectionResult{
            Language:   bestLang,
            Confidence: bestScore * 0.85,
            Stage:      StageKeywords,
            Entry:      d.catalog.byLanguage[bestLang],
        }
    }

    return DetectionResult{Language: "text", Confidence: 0.1, Stage: StageFallback}
	// Implementação simplificada: pular extensão, ir direto para shebang/keywords
	if strings.HasPrefix(content, "#!") {
		// Extrair shebang da primeira linha
		lines := strings.SplitN(content, "\n", 2)
		firstLine := lines[0]
		matches := d.shebangRegex.FindStringSubmatch(firstLine)
		if len(matches) >= 2 {
			interpreter := strings.ToLower(matches[1])
			for _, entry := range d.catalog.byLanguage {
				for _, sb := range entry.Shebang {
					if strings.Contains(interpreter, strings.ToLower(sb)) {
						return DetectionResult{
							Language:   entry.Language,
							Confidence: 0.90,
							Stage:      StageShebang,
							Evidence:   []string{"shebang:" + interpreter},
							Entry:      entry,
						}
					}
				}
			}
		}
	}

	// Detectar por keywords
	return d.detectByKeywordsContent(content)
}

func (d *UniversalLanguageDetector) detectByKeywordsContent(content string) DetectionResult {
	bestLang := ""
	bestScore := 0.0

	for lang, regexes := range d.keywordRegexes {
		score := 0.0
		for _, re := range regexes {
			if re.MatchString(content) {
				score += 1.0 / float64(len(regexes))
			}
		}
		if score > bestScore && score >= 0.3 {
			bestScore = score
			bestLang = lang
		}
	}

	if bestLang != "" {
		return DetectionResult{
			Language:   bestLang,
			Confidence: bestScore * 0.85,
			Stage:      StageKeywords,
			Entry:      d.catalog.byLanguage[bestLang],
		}
	}

	return DetectionResult{Language: "text", Confidence: 0.1, Stage: StageFallback}
}
