// universal_detector.go — Detecção de linguagem por conteúdo e extensão
package arkhe

import (
    "os"
    "path/filepath"
    "strings"
    "sync"
)

// LanguageDetector identifica a linguagem de um arquivo
type LanguageDetector struct {
    catalog *LanguageCatalog
    mu      sync.Mutex
}

func NewLanguageDetector(catalog *LanguageCatalog) *LanguageDetector {
    return &LanguageDetector{catalog: catalog}
}

// Detect determina a linguagem de um arquivo com confiança
func (ld *LanguageDetector) Detect(filePath string) (string, float64) {
    // Etapa 1: Extensão do arquivo
    ext := strings.ToLower(filepath.Ext(filePath))
    // Arquivos especiais sem extensão
    baseName := filepath.Base(filePath)
    specialFiles := map[string]string{
        "Dockerfile":       "dockerfile",
        "Makefile":         "makefile",
        "CMakeLists.txt":   "cmake",
        "Vagrantfile":      "ruby",
        "Rakefile":         "ruby",
        "Gemfile":          "ruby",
        "Procfile":         "yaml",
        ".bashrc":          "shell",
        ".zshrc":           "shell",
        ".vimrc":           "vim",
        ".gitignore":       "gitignore",
        "LICENSE":          "text",
        "README":           "markdown",
    }
    if lang, ok := specialFiles[baseName]; ok {
        return lang, 0.95
    }

    // Consultar catálogo
    if entry, ok := ld.catalog.entries[ext]; ok {
        return entry.Language, 0.90
    }

    // Etapa 2: Shebang (primeira linha)
    if content, err := os.ReadFile(filePath); err == nil {
        firstLine := strings.TrimSpace(strings.Split(string(content), "\n")[0])
        if strings.HasPrefix(firstLine, "#!") {
            shebang := strings.TrimPrefix(firstLine, "#!")
            shebang = strings.TrimSpace(shebang)
            // Extrair o interpretador
            parts := strings.Fields(shebang)
            if len(parts) > 0 {
                interpreter := filepath.Base(parts[0])
                for _, entry := range ld.catalog.entries {
                    for _, sb := range entry.Shebang {
                        if strings.Contains(interpreter, sb) {
                            return entry.Language, 0.95
                        }
                    }
                }
            }
            return parts[0], 0.80 // Retornar o comando se não achar no catálogo
        }

        // Etapa 3: Palavras-chave únicas (amostra das primeiras 50 linhas)
        lines := strings.Split(string(content), "\n")
        sampleSize := 50
        if len(lines) < sampleSize {
            sampleSize = len(lines)
        }
        sample := strings.Join(lines[:sampleSize], "\n")

        bestMatch := "text"
        bestScore := 0.0

        for _, entry := range ld.catalog.entries {
            if len(entry.Keywords) == 0 {
                continue
            }
            score := 0.0
            for _, kw := range entry.Keywords {
                if strings.Contains(sample, kw) {
                    score += 1.0 / float64(len(entry.Keywords))
                }
            }
            if score > bestScore {
                bestScore = score
                bestMatch = entry.Language
            }
        }
        if bestScore > 0.3 {
            return bestMatch, bestScore
        }
    }

    return "text", 0.1
}
