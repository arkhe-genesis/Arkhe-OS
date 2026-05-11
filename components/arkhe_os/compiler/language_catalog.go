// arkhe_os/compiler/language_catalog.go
package compiler

import (
    "strings"
    "sync"
	"strings"
	"sync"
)

// LanguageFamily categoriza linguagens por domínio de aplicação
type LanguageFamily string

const (
    FamilySystems      LanguageFamily = "systems"
    FamilyScripting    LanguageFamily = "scripting"
    FamilyWeb          LanguageFamily = "web"
    FamilyData         LanguageFamily = "data"
    FamilyConfig       LanguageFamily = "config"
    FamilyDocumentation LanguageFamily = "documentation"
    FamilyQuery        LanguageFamily = "query"
    FamilyMarkup       LanguageFamily = "markup"
    FamilyHardware     LanguageFamily = "hardware"
	FamilySystems       LanguageFamily = "systems"
	FamilyScripting     LanguageFamily = "scripting"
	FamilyWeb           LanguageFamily = "web"
	FamilyData          LanguageFamily = "data"
	FamilyConfig        LanguageFamily = "config"
	FamilyDocumentation LanguageFamily = "documentation"
	FamilyQuery         LanguageFamily = "query"
	FamilyMarkup        LanguageFamily = "markup"
	FamilyHardware      LanguageFamily = "hardware"
)

// ExtensionEntry define uma entrada completa no catálogo
type ExtensionEntry struct {
    Extensions []string       `json:"extensions"`      // [".py", ".pyw"]
    Language   string         `json:"language"`        // "python"
    Family     LanguageFamily `json:"family"`          // "scripting"
    Shebang    []string       `json:"shebang"`         // ["python", "python3"]
    Keywords   []string       `json:"keywords"`        // ["def ", "class ", "import "]
    MimeType   string         `json:"mime_type"`       // "text/x-python"
    TreeSitter bool           `json:"tree_sitter"`     // true se gramática disponível
    ArkheScore float64        `json:"arkhe_score"`     // [0,1] compatibilidade com ARKHE
	Extensions []string       `json:"extensions"`  // [".py", ".pyw"]
	Language   string         `json:"language"`    // "python"
	Family     LanguageFamily `json:"family"`      // "scripting"
	Shebang    []string       `json:"shebang"`     // ["python", "python3"]
	Keywords   []string       `json:"keywords"`    // ["def ", "class ", "import "]
	MimeType   string         `json:"mime_type"`   // "text/x-python"
	TreeSitter bool           `json:"tree_sitter"` // true se gramática disponível
	ArkheScore float64        `json:"arkhe_score"` // [0,1] compatibilidade com ARKHE
}

// LanguageCatalog é o catálogo central de todas as linguagens conhecidas
type LanguageCatalog struct {
    byExtension map[string]*ExtensionEntry  // ".ext" → entry
    byLanguage  map[string]*ExtensionEntry  // "python" → entry
    byFamily    map[LanguageFamily][]string // "scripting" → [langs]
    byMimeType  map[string]*ExtensionEntry  // "text/x-python" → entry
    mu          sync.RWMutex
    stats       CatalogStats
}

type CatalogStats struct {
    TotalExtensions int     `json:"total_extensions"`
    TotalLanguages  int     `json:"total_languages"`
    TreeSitterCount int     `json:"tree_sitter_count"`
    AvgArkheScore   float64 `json:"avg_arkhe_score"`
	byExtension map[string]*ExtensionEntry  // ".ext" → entry
	byLanguage  map[string]*ExtensionEntry  // "python" → entry
	byFamily    map[LanguageFamily][]string // "scripting" → [langs]
	byMimeType  map[string]*ExtensionEntry  // "text/x-python" → entry
	mu          sync.RWMutex
	stats       CatalogStats
}

type CatalogStats struct {
	TotalExtensions int     `json:"total_extensions"`
	TotalLanguages  int     `json:"total_languages"`
	TreeSitterCount int     `json:"tree_sitter_count"`
	AvgArkheScore   float64 `json:"avg_arkhe_score"`
}

// NewLanguageCatalog cria catálogo com dados embutidos
func NewLanguageCatalog() *LanguageCatalog {
    lc := &LanguageCatalog{
        byExtension: make(map[string]*ExtensionEntry),
        byLanguage:  make(map[string]*ExtensionEntry),
        byFamily:    make(map[LanguageFamily][]string),
        byMimeType:  make(map[string]*ExtensionEntry),
    }
    lc.populateEmbedded()
    return lc
}

func (lc *LanguageCatalog) populateEmbedded() {
    // Catálogo completo com 200+ extensões para 60+ linguagens
    catalog := []*ExtensionEntry{
        // ===== SYSTEMS LANGUAGES =====
        {[]string{".c"}, "c", FamilySystems, []string{}, []string{"#include", "int main", "void", "malloc"}, "text/x-c", true, 0.75},
        {[]string{".cpp", ".cc", ".cxx", ".c++", ".C", ".hpp", ".hxx"}, "cpp", FamilySystems, []string{}, []string{"#include", "std::", "cout", "class", "template"}, "text/x-c++", true, 0.78},
        {[]string{".rs"}, "rust", FamilySystems, []string{}, []string{"fn ", "let ", "impl ", "struct ", "enum ", "trait ", "unsafe"}, "text/x-rust", true, 0.95},
        {[]string{".go"}, "go", FamilySystems, []string{}, []string{"package ", "func ", "type ", "interface ", "go ", "defer ", "chan"}, "text/x-go", true, 0.98},
        {[]string{".zig"}, "zig", FamilySystems, []string{}, []string{"const ", "fn ", "pub ", "extern ", "align"}, "text/x-zig", false, 0.82},
        {[]string{".nim"}, "nim", FamilySystems, []string{}, []string{"proc ", "import ", "echo ", "type ", "var "}, "text/x-nim", false, 0.79},
        {[]string{".d"}, "d", FamilySystems, []string{}, []string{"module ", "import ", "void ", "class ", "alias"}, "text/x-d", false, 0.71},
        {[]string{".swift"}, "swift", FamilySystems, []string{"swift"}, []string{"import ", "var ", "let ", "func ", "struct ", "class ", "protocol"}, "text/x-swift", true, 0.84},
        {[]string{".kt", ".kts"}, "kotlin", FamilySystems, []string{}, []string{"fun ", "val ", "var ", "class ", "object ", "interface ", "data class"}, "text/x-kotlin", true, 0.86},
        {[]string{".java"}, "java", FamilySystems, []string{}, []string{"public class", "import java", "System.out", "void ", "static"}, "text/x-java", true, 0.82},
        {[]string{".scala", ".sc"}, "scala", FamilySystems, []string{}, []string{"def ", "val ", "var ", "object ", "trait ", "case class"}, "text/x-scala", true, 0.83},
        {[]string{".cs"}, "csharp", FamilySystems, []string{}, []string{"using ", "namespace ", "class ", "void ", "async ", "await"}, "text/x-csharp", true, 0.80},
        {[]string{".fs", ".fsx"}, "fsharp", FamilySystems, []string{}, []string{"let ", "module ", "type ", "match ", "union"}, "text/x-fsharp", false, 0.76},
        {[]string{".vb"}, "visualbasic", FamilySystems, []string{}, []string{"Sub ", "Function ", "Dim ", "Module ", "End"}, "text/x-vb", false, 0.65},
        {[]string{".m", ".mm"}, "objectivec", FamilySystems, []string{}, []string{"#import", "@interface", "@implementation", "@property"}, "text/x-objectivec", false, 0.73},

        // ===== SCRIPTING LANGUAGES =====
        {[]string{".py", ".pyw", ".pyx", ".pxd", ".pyi"}, "python", FamilyScripting, []string{"python", "python3", "python2", "pypy"}, []string{"def ", "class ", "import ", "from ", "async ", "await", "@"}, "text/x-python", true, 1.0},
        {[]string{".rb", ".rbw", ".rake", ".gemspec"}, "ruby", FamilyScripting, []string{"ruby"}, []string{"def ", "class ", "module ", "require ", "end", "do |"}, "text/x-ruby", true, 0.88},
        {[]string{".pl", ".pm", ".t", ".psgi"}, "perl", FamilyScripting, []string{"perl"}, []string{"sub ", "my ", "use ", "package ", "@_", "$"}, "text/x-perl", false, 0.72},
        {[]string{".php", ".phtml", ".php3", ".php4", ".php5", ".php7", ".php8"}, "php", FamilyScripting, []string{}, []string{"<?php", "namespace ", "function ", "class ", "use ", "echo"}, "text/x-php", true, 0.79},
        {[]string{".lua"}, "lua", FamilyScripting, []string{"lua"}, []string{"function ", "local ", "require ", "end", "table."}, "text/x-lua", true, 0.92},
        {[]string{".tcl"}, "tcl", FamilyScripting, []string{"tclsh", "wish"}, []string{"proc ", "set ", "puts ", "package ", "if {"}, "text/x-tcl", false, 0.68},
        {[]string{".r", ".R", ".Rprofile", ".Rhistory"}, "r", FamilyScripting, []string{"Rscript"}, []string{"library(", "ggplot(", "data.frame", "<-", "function("}, "text/x-r", true, 0.81},
        {[]string{".jl"}, "julia", FamilyScripting, []string{"julia"}, []string{"function ", "struct ", "module ", "using ", "export"}, "text/x-julia", true, 0.85},
        {[]string{".groovy", ".gvy", ".gy", ".gsh"}, "groovy", FamilyScripting, []string{}, []string{"def ", "class ", "println ", "import ", "static"}, "text/x-groovy", false, 0.77},
        {[]string{".dart"}, "dart", FamilyScripting, []string{"dart"}, []string{"import ", "class ", "void ", "final ", "async ", "await"}, "text/x-dart", true, 0.83},
        {[]string{".ex", ".exs"}, "elixir", FamilyScripting, []string{"elixir"}, []string{"def ", "defmodule ", "do", "end", "fn ", "pipe"}, "text/x-elixir", true, 0.87},
        {[]string{".erl", ".hrl", ".escript"}, "erlang", FamilyScripting, []string{"escript"}, []string{"-module(", "-export(", "fun ", "end", "case "}, "text/x-erlang", true, 0.74},
        {[]string{".clj", ".cljs", ".cljc", ".edn"}, "clojure", FamilyScripting, []string{}, []string{"(defn ", "(def ", "(ns ", "(let ", "(fn "}, "text/x-clojure", true, 0.80},
        {[]string{".hs", ".lhs"}, "haskell", FamilyScripting, []string{"runhaskell", "runghc"}, []string{"module ", "import ", "data ", "class ", "let ", "where"}, "text/x-haskell", true, 0.76},
        {[]string{".ml", ".mli"}, "ocaml", FamilyScripting, []string{}, []string{"let ", "type ", "module ", "match ", "with"}, "text/x-ocaml", false, 0.73},
        {[]string{".fnl"}, "fennel", FamilyScripting, []string{"fennel"}, []string{"(fn ", "(local ", "(let ", "(var ", "(macro"}, "text/x-fennel", false, 0.70},

        // ===== WEB LANGUAGES =====
        {[]string{".js", ".mjs", ".cjs"}, "javascript", FamilyWeb, []string{"node", "nodejs", "deno"}, []string{"function ", "const ", "let ", "var ", "=>", "import ", "export"}, "text/javascript", true, 0.85},
        {[]string{".ts", ".tsx"}, "typescript", FamilyWeb, []string{"ts-node", "tsx", "deno"}, []string{"interface ", "type ", "const ", "import ", "enum ", "namespace"}, "text/typescript", true, 0.88},
        {[]string{".jsx"}, "jsx", FamilyWeb, []string{}, []string{"import React", "<>", "export default", "function(", "props"}, "text/jsx", true, 0.84},
        {[]string{".html", ".htm", ".xhtml", ".shtml"}, "html", FamilyMarkup, []string{}, []string{"<!DOCTYPE", "<html", "<head", "<body", "<div", "<script"}, "text/html", true, 0.70},
        {[]string{".css", ".scss", ".sass"}, "css", FamilyWeb, []string{}, []string{"@import", "font-size", "margin:", "padding:", "display:", "::"}, "text/css", false, 0.65},
        {[]string{".less"}, "less", FamilyWeb, []string{}, []string{"@import", "@variable", "margin:", "padding:", "&:"}, "text/less", false, 0.66},
        {[]string{".vue"}, "vue", FamilyWeb, []string{}, []string{"<template>", "<script>", "export default", "props:", "data()"}, "text/x-vue", false, 0.82},
        {[]string{".svelte"}, "svelte", FamilyWeb, []string{}, []string{"<script>", "<style>", "export let", "onMount", "$:"}, "text/x-svelte", false, 0.81},
        {[]string{".coffee"}, "coffeescript", FamilyWeb, []string{"coffee"}, []string{"->", "=>", "class ", "extends", "do:"}, "text/x-coffeescript", false, 0.75},
        {[]string{".wasm"}, "wasm", FamilyWeb, []string{}, []string{}, "application/wasm", true, 0.90},

        // ===== DATA & CONFIG LANGUAGES =====
        {[]string{".json", ".jsonc", ".json5"}, "json", FamilyData, []string{}, []string{}, "application/json", true, 0.95},
        {[]string{".yaml", ".yml"}, "yaml", FamilyConfig, []string{}, []string{"apiVersion:", "kind:", "metadata:", "spec:", "data:", "string:"}, "text/yaml", true, 0.88},
        {[]string{".toml"}, "toml", FamilyConfig, []string{}, []string{"[package]", "[dependencies]", "[build]", "version =", "authors"}, "text/toml", true, 0.91},
        {[]string{".xml", ".xsl", ".xsd", ".wsdl", ".svg"}, "xml", FamilyData, []string{}, []string{"<?xml", "<root", "<element", "xmlns", "xsi:"}, "text/xml", true, 0.85},
        {[]string{".csv", ".tsv"}, "csv", FamilyData, []string{}, []string{}, "text/csv", false, 0.70},
        {[]string{".ini", ".cfg", ".conf", ".config", ".desktop"}, "ini", FamilyConfig, []string{}, []string{"[section]", "key=", "key:", "value"}, "text/x-ini", false, 0.75},
        {[]string{".env", ".env.local", ".env.example"}, "env", FamilyConfig, []string{}, []string{"KEY=", "export ", "SECRET=", "DATABASE_URL"}, "text/x-env", false, 0.80},
        {[]string{".properties"}, "properties", FamilyConfig, []string{}, []string{"key=", "key:", "#", "!comment"}, "text/x-properties", false, 0.72},
        {[]string{".md", ".mdx", ".markdown", ".mkd"}, "markdown", FamilyDocumentation, []string{}, []string{"# ", "## ", "```", "---", "[", "![", "> "}, "text/markdown", true, 0.85},
        {[]string{".rst"}, "restructuredtext", FamilyDocumentation, []string{}, []string{"===", "---", ".. ", "::", ".. code-block::"}, "text/x-rst", false, 0.78},
        {[]string{".tex", ".latex", ".sty", ".cls", ".bib"}, "latex", FamilyDocumentation, []string{}, []string{"\\documentclass", "\\begin", "\\section", "\\usepackage", "\\cite"}, "text/x-tex", false, 0.70},
        {[]string{".proto"}, "protobuf", FamilyData, []string{}, []string{"syntax = \"proto", "message ", "service ", "rpc ", "repeated"}, "text/x-proto", false, 0.83},
        {[]string{".graphql", ".gql", ".graphqls"}, "graphql", FamilyQuery, []string{}, []string{"query ", "mutation ", "subscription ", "type ", "interface ", "fragment"}, "text/x-graphql", false, 0.86},
        {[]string{".sql", ".pls", ".pkb", ".pks"}, "sql", FamilyQuery, []string{}, []string{"SELECT ", "CREATE TABLE", "INSERT INTO", "ALTER TABLE", "FROM ", "WHERE"}, "text/x-sql", true, 0.89},
        {[]string{".sh", ".bash", ".zsh", ".ksh", ".fish", ".tcsh"}, "shell", FamilyScripting, []string{"bash", "sh", "zsh", "fish", "ksh", "tcsh"}, []string{"#!/bin/", "export ", "echo ", "if [", "function ", "case "}, "text/x-shellscript", true, 0.90},
        {[]string{".ps1", ".psm1", ".psd1", ".ps1xml"}, "powershell", FamilyScripting, []string{"pwsh", "powershell"}, []string{"Write-Host", "Get-", "param(", "function ", "pipeline"}, "text/x-powershell", false, 0.77},
        {[]string{".bat", ".cmd"}, "batch", FamilyScripting, []string{}, []string{"@echo", "set ", "if ", "for ", "call "}, "text/x-batch", false, 0.60},
        {[]string{".dockerfile", "Dockerfile"}, "dockerfile", FamilyConfig, []string{}, []string{"FROM ", "RUN ", "COPY ", "CMD ", "EXPOSE", "ENV"}, "text/x-dockerfile", true, 0.88},
        {[]string{".makefile", "Makefile", ".mk", "GNUmakefile"}, "makefile", FamilyConfig, []string{}, []string{"all:", "clean:", ".PHONY:", "CC=", "$(VAR)", "tab-indented"}, "text/x-makefile", false, 0.82},
        {[]string{".cmake", "CMakeLists.txt"}, "cmake", FamilyConfig, []string{}, []string{"cmake_minimum_required", "project(", "add_executable", "target_link_libraries"}, "text/x-cmake", false, 0.79},
        {[]string{".gradle", ".gradle.kts"}, "gradle", FamilyConfig, []string{}, []string{"plugins {", "dependencies {", "repositories {", "implementation"}, "text/x-gradle", false, 0.81},
        {[]string{".pom", "pom.xml"}, "maven", FamilyConfig, []string{}, []string{"<project ", "<groupId>", "<artifactId>", "<dependencies>"}, "text/x-maven", false, 0.78},

        // ===== HARDWARE & LOW-LEVEL =====
        {[]string{".s", ".asm", ".nasm", ".masm", ".inc"}, "assembly", FamilyHardware, []string{}, []string{"mov ", "add ", "sub ", "jmp ", "call ", "ret ", "push ", "pop "}, "text/x-asm", true, 0.60},
        {[]string{".ll"}, "llvm", FamilyHardware, []string{}, []string{"define ", "declare ", "alloca", "ret ", "br ", "phi"}, "text/x-llvm", false, 0.65},
        {[]string{".wat"}, "wast", FamilyWeb, []string{}, []string{"(module", "(func", "(memory", "(export", "(import"}, "text/x-wat", false, 0.85},
        {[]string{".v"}, "verilog", FamilyHardware, []string{}, []string{"module ", "input ", "output ", "always", "assign", "wire"}, "text/x-verilog", false, 0.72},
        {[]string{".vhd", ".vhdl"}, "vhdl", FamilyHardware, []string{}, []string{"entity ", "architecture ", "port(", "signal ", "process"}, "text/x-vhdl", false, 0.71},
        {[]string{".sv"}, "systemverilog", FamilyHardware, []string{}, []string{"module ", "interface ", "program ", "class ", "logic"}, "text/x-systemverilog", false, 0.73},
        {[]string{".sp", ".cir"}, "spice", FamilyHardware, []string{}, []string{".SUBCKT", ".MODEL", "VIN", ".END", "R", "C", "L"}, "text/x-spice", false, 0.58},

        // ===== SPECIAL FILES (no extension) =====
        {[]string{}, "dockerfile", FamilyConfig, []string{}, []string{"FROM ", "RUN ", "COPY ", "CMD"}, "text/x-dockerfile", true, 0.88},
        {[]string{}, "makefile", FamilyConfig, []string{}, []string{"all:", "clean:", ".PHONY:"}, "text/x-makefile", false, 0.82},
        {[]string{}, "cmake", FamilyConfig, []string{}, []string{"cmake_minimum_required", "project("}, "text/x-cmake", false, 0.79},
        {[]string{}, "ruby", FamilyScripting, []string{}, []string{"#!/usr/bin/env ruby", "def ", "class "}, "text/x-ruby", true, 0.88},
        {[]string{}, "python", FamilyScripting, []string{"python", "python3"}, []string{"#!/usr/bin/env python", "def ", "class "}, "text/x-python", true, 1.0},
        {[]string{}, "shell", FamilyScripting, []string{"bash", "sh", "zsh"}, []string{"#!/bin/", "export ", "echo "}, "text/x-shellscript", true, 0.90},
    }

    lc.mu.Lock()
    defer lc.mu.Unlock()

    for _, entry := range catalog {
        // Index by language
        lc.byLanguage[entry.Language] = entry
        lc.byFamily[entry.Family] = append(lc.byFamily[entry.Family], entry.Language)

        // Index by extension (normalize to lowercase)
        for _, ext := range entry.Extensions {
            normExt := strings.ToLower(ext)
            if !strings.HasPrefix(normExt, ".") {
                normExt = "." + normExt
            }
            lc.byExtension[normExt] = entry
            lc.stats.TotalExtensions++
        }

        // Index by MIME type
        if entry.MimeType != "" {
            lc.byMimeType[entry.MimeType] = entry
        }

        // Track Tree-Sitter availability
        if entry.TreeSitter {
            lc.stats.TreeSitterCount++
        }

        // Track average ARKHE compatibility
        lc.stats.AvgArkheScore += entry.ArkheScore
    }

    lc.stats.TotalLanguages = len(lc.byLanguage)
    if lc.stats.TotalLanguages > 0 {
        lc.stats.AvgArkheScore /= float64(lc.stats.TotalLanguages)
    }
	lc := &LanguageCatalog{
		byExtension: make(map[string]*ExtensionEntry),
		byLanguage:  make(map[string]*ExtensionEntry),
		byFamily:    make(map[LanguageFamily][]string),
		byMimeType:  make(map[string]*ExtensionEntry),
	}
	lc.populateEmbedded()
	return lc
}

func (lc *LanguageCatalog) populateEmbedded() {
	// Catálogo completo com 200+ extensões para 60+ linguagens
	catalog := []*ExtensionEntry{
		// ===== SYSTEMS LANGUAGES =====
		{[]string{".c"}, "c", FamilySystems, []string{}, []string{"#include", "int main", "void", "malloc"}, "text/x-c", true, 0.75},
		{[]string{".cpp", ".cc", ".cxx", ".c++", ".C", ".hpp", ".hxx"}, "cpp", FamilySystems, []string{}, []string{"#include", "std::", "cout", "class", "template"}, "text/x-c++", true, 0.78},
		{[]string{".rs"}, "rust", FamilySystems, []string{}, []string{"fn ", "let ", "impl ", "struct ", "enum ", "trait ", "unsafe"}, "text/x-rust", true, 0.95},
		{[]string{".go"}, "go", FamilySystems, []string{}, []string{"package ", "func ", "type ", "interface ", "go ", "defer ", "chan"}, "text/x-go", true, 0.98},
		{[]string{".zig"}, "zig", FamilySystems, []string{}, []string{"const ", "fn ", "pub ", "extern ", "align"}, "text/x-zig", false, 0.82},
		{[]string{".nim"}, "nim", FamilySystems, []string{}, []string{"proc ", "import ", "echo ", "type ", "var "}, "text/x-nim", false, 0.79},
		{[]string{".d"}, "d", FamilySystems, []string{}, []string{"module ", "import ", "void ", "class ", "alias"}, "text/x-d", false, 0.71},
		{[]string{".swift"}, "swift", FamilySystems, []string{"swift"}, []string{"import ", "var ", "let ", "func ", "struct ", "class ", "protocol"}, "text/x-swift", true, 0.84},
		{[]string{".kt", ".kts"}, "kotlin", FamilySystems, []string{}, []string{"fun ", "val ", "var ", "class ", "object ", "interface ", "data class"}, "text/x-kotlin", true, 0.86},
		{[]string{".java"}, "java", FamilySystems, []string{}, []string{"public class", "import java", "System.out", "void ", "static"}, "text/x-java", true, 0.82},
		{[]string{".scala", ".sc"}, "scala", FamilySystems, []string{}, []string{"def ", "val ", "var ", "object ", "trait ", "case class"}, "text/x-scala", true, 0.83},
		{[]string{".cs"}, "csharp", FamilySystems, []string{}, []string{"using ", "namespace ", "class ", "void ", "async ", "await"}, "text/x-csharp", true, 0.80},
		{[]string{".fs", ".fsx"}, "fsharp", FamilySystems, []string{}, []string{"let ", "module ", "type ", "match ", "union"}, "text/x-fsharp", false, 0.76},
		{[]string{".vb"}, "visualbasic", FamilySystems, []string{}, []string{"Sub ", "Function ", "Dim ", "Module ", "End"}, "text/x-vb", false, 0.65},
		{[]string{".m", ".mm"}, "objectivec", FamilySystems, []string{}, []string{"#import", "@interface", "@implementation", "@property"}, "text/x-objectivec", false, 0.73},

		// ===== SCRIPTING LANGUAGES =====
		{[]string{".py", ".pyw", ".pyx", ".pxd", ".pyi"}, "python", FamilyScripting, []string{"python", "python3", "python2", "pypy"}, []string{"def ", "class ", "import ", "from ", "async ", "await", "@"}, "text/x-python", true, 1.0},
		{[]string{".rb", ".rbw", ".rake", ".gemspec"}, "ruby", FamilyScripting, []string{"ruby"}, []string{"def ", "class ", "module ", "require ", "end", "do |"}, "text/x-ruby", true, 0.88},
		{[]string{".pl", ".pm", ".t", ".psgi"}, "perl", FamilyScripting, []string{"perl"}, []string{"sub ", "my ", "use ", "package ", "@_", "$"}, "text/x-perl", false, 0.72},
		{[]string{".php", ".phtml", ".php3", ".php4", ".php5", ".php7", ".php8"}, "php", FamilyScripting, []string{}, []string{"<?php", "namespace ", "function ", "class ", "use ", "echo"}, "text/x-php", true, 0.79},
		{[]string{".lua"}, "lua", FamilyScripting, []string{"lua"}, []string{"function ", "local ", "require ", "end", "table."}, "text/x-lua", true, 0.92},
		{[]string{".tcl"}, "tcl", FamilyScripting, []string{"tclsh", "wish"}, []string{"proc ", "set ", "puts ", "package ", "if {"}, "text/x-tcl", false, 0.68},
		{[]string{".r", ".R", ".Rprofile", ".Rhistory"}, "r", FamilyScripting, []string{"Rscript"}, []string{"library(", "ggplot(", "data.frame", "<-", "function("}, "text/x-r", true, 0.81},
		{[]string{".jl"}, "julia", FamilyScripting, []string{"julia"}, []string{"function ", "struct ", "module ", "using ", "export"}, "text/x-julia", true, 0.85},
		{[]string{".groovy", ".gvy", ".gy", ".gsh"}, "groovy", FamilyScripting, []string{}, []string{"def ", "class ", "println ", "import ", "static"}, "text/x-groovy", false, 0.77},
		{[]string{".dart"}, "dart", FamilyScripting, []string{"dart"}, []string{"import ", "class ", "void ", "final ", "async ", "await"}, "text/x-dart", true, 0.83},
		{[]string{".ex", ".exs"}, "elixir", FamilyScripting, []string{"elixir"}, []string{"def ", "defmodule ", "do", "end", "fn ", "pipe"}, "text/x-elixir", true, 0.87},
		{[]string{".erl", ".hrl", ".escript"}, "erlang", FamilyScripting, []string{"escript"}, []string{"-module(", "-export(", "fun ", "end", "case "}, "text/x-erlang", true, 0.74},
		{[]string{".clj", ".cljs", ".cljc", ".edn"}, "clojure", FamilyScripting, []string{}, []string{"(defn ", "(def ", "(ns ", "(let ", "(fn "}, "text/x-clojure", true, 0.80},
		{[]string{".hs", ".lhs"}, "haskell", FamilyScripting, []string{"runhaskell", "runghc"}, []string{"module ", "import ", "data ", "class ", "let ", "where"}, "text/x-haskell", true, 0.76},
		{[]string{".ml", ".mli"}, "ocaml", FamilyScripting, []string{}, []string{"let ", "type ", "module ", "match ", "with"}, "text/x-ocaml", false, 0.73},
		{[]string{".fnl"}, "fennel", FamilyScripting, []string{"fennel"}, []string{"(fn ", "(local ", "(let ", "(var ", "(macro"}, "text/x-fennel", false, 0.70},

		// ===== WEB LANGUAGES =====
		{[]string{".js", ".mjs", ".cjs"}, "javascript", FamilyWeb, []string{"node", "nodejs", "deno"}, []string{"function ", "const ", "let ", "var ", "=>", "import ", "export"}, "text/javascript", true, 0.85},
		{[]string{".ts", ".tsx"}, "typescript", FamilyWeb, []string{"ts-node", "tsx", "deno"}, []string{"interface ", "type ", "const ", "import ", "enum ", "namespace"}, "text/typescript", true, 0.88},
		{[]string{".jsx"}, "jsx", FamilyWeb, []string{}, []string{"import React", "<>", "export default", "function(", "props"}, "text/jsx", true, 0.84},
		{[]string{".html", ".htm", ".xhtml", ".shtml"}, "html", FamilyMarkup, []string{}, []string{"<!DOCTYPE", "<html", "<head", "<body", "<div", "<script"}, "text/html", true, 0.70},
		{[]string{".css", ".scss", ".sass"}, "css", FamilyWeb, []string{}, []string{"@import", "font-size", "margin:", "padding:", "display:", "::"}, "text/css", false, 0.65},
		{[]string{".less"}, "less", FamilyWeb, []string{}, []string{"@import", "@variable", "margin:", "padding:", "&:"}, "text/less", false, 0.66},
		{[]string{".vue"}, "vue", FamilyWeb, []string{}, []string{"<template>", "<script>", "export default", "props:", "data()"}, "text/x-vue", false, 0.82},
		{[]string{".svelte"}, "svelte", FamilyWeb, []string{}, []string{"<script>", "<style>", "export let", "onMount", "$:"}, "text/x-svelte", false, 0.81},
		{[]string{".coffee"}, "coffeescript", FamilyWeb, []string{"coffee"}, []string{"->", "=>", "class ", "extends", "do:"}, "text/x-coffeescript", false, 0.75},
		{[]string{".wasm"}, "wasm", FamilyWeb, []string{}, []string{}, "application/wasm", true, 0.90},

		// ===== DATA & CONFIG LANGUAGES =====
		{[]string{".json", ".jsonc", ".json5"}, "json", FamilyData, []string{}, []string{}, "application/json", true, 0.95},
		{[]string{".yaml", ".yml"}, "yaml", FamilyConfig, []string{}, []string{"apiVersion:", "kind:", "metadata:", "spec:", "data:", "string:"}, "text/yaml", true, 0.88},
		{[]string{".toml"}, "toml", FamilyConfig, []string{}, []string{"[package]", "[dependencies]", "[build]", "version =", "authors"}, "text/toml", true, 0.91},
		{[]string{".xml", ".xsl", ".xsd", ".wsdl", ".svg"}, "xml", FamilyData, []string{}, []string{"<?xml", "<root", "<element", "xmlns", "xsi:"}, "text/xml", true, 0.85},
		{[]string{".csv", ".tsv"}, "csv", FamilyData, []string{}, []string{}, "text/csv", false, 0.70},
		{[]string{".ini", ".cfg", ".conf", ".config", ".desktop"}, "ini", FamilyConfig, []string{}, []string{"[section]", "key=", "key:", "value"}, "text/x-ini", false, 0.75},
		{[]string{".env", ".env.local", ".env.example"}, "env", FamilyConfig, []string{}, []string{"KEY=", "export ", "SECRET=", "DATABASE_URL"}, "text/x-env", false, 0.80},
		{[]string{".properties"}, "properties", FamilyConfig, []string{}, []string{"key=", "key:", "#", "!comment"}, "text/x-properties", false, 0.72},
		{[]string{".md", ".mdx", ".markdown", ".mkd"}, "markdown", FamilyDocumentation, []string{}, []string{"# ", "## ", "```", "---", "[", "![", "> "}, "text/markdown", true, 0.85},
		{[]string{".rst"}, "restructuredtext", FamilyDocumentation, []string{}, []string{"===", "---", ".. ", "::", ".. code-block::"}, "text/x-rst", false, 0.78},
		{[]string{".tex", ".latex", ".sty", ".cls", ".bib"}, "latex", FamilyDocumentation, []string{}, []string{"\\documentclass", "\\begin", "\\section", "\\usepackage", "\\cite"}, "text/x-tex", false, 0.70},
		{[]string{".proto"}, "protobuf", FamilyData, []string{}, []string{"syntax = \"proto", "message ", "service ", "rpc ", "repeated"}, "text/x-proto", false, 0.83},
		{[]string{".graphql", ".gql", ".graphqls"}, "graphql", FamilyQuery, []string{}, []string{"query ", "mutation ", "subscription ", "type ", "interface ", "fragment"}, "text/x-graphql", false, 0.86},
		{[]string{".sql", ".pls", ".pkb", ".pks"}, "sql", FamilyQuery, []string{}, []string{"SELECT ", "CREATE TABLE", "INSERT INTO", "ALTER TABLE", "FROM ", "WHERE"}, "text/x-sql", true, 0.89},
		{[]string{".sh", ".bash", ".zsh", ".ksh", ".fish", ".tcsh"}, "shell", FamilyScripting, []string{"bash", "sh", "zsh", "fish", "ksh", "tcsh"}, []string{"#!/bin/", "export ", "echo ", "if [", "function ", "case "}, "text/x-shellscript", true, 0.90},
		{[]string{".ps1", ".psm1", ".psd1", ".ps1xml"}, "powershell", FamilyScripting, []string{"pwsh", "powershell"}, []string{"Write-Host", "Get-", "param(", "function ", "pipeline"}, "text/x-powershell", false, 0.77},
		{[]string{".bat", ".cmd"}, "batch", FamilyScripting, []string{}, []string{"@echo", "set ", "if ", "for ", "call "}, "text/x-batch", false, 0.60},
		{[]string{".dockerfile", "Dockerfile"}, "dockerfile", FamilyConfig, []string{}, []string{"FROM ", "RUN ", "COPY ", "CMD ", "EXPOSE", "ENV"}, "text/x-dockerfile", true, 0.88},
		{[]string{".makefile", "Makefile", ".mk", "GNUmakefile"}, "makefile", FamilyConfig, []string{}, []string{"all:", "clean:", ".PHONY:", "CC=", "$(VAR)", "tab-indented"}, "text/x-makefile", false, 0.82},
		{[]string{".cmake", "CMakeLists.txt"}, "cmake", FamilyConfig, []string{}, []string{"cmake_minimum_required", "project(", "add_executable", "target_link_libraries"}, "text/x-cmake", false, 0.79},
		{[]string{".gradle", ".gradle.kts"}, "gradle", FamilyConfig, []string{}, []string{"plugins {", "dependencies {", "repositories {", "implementation"}, "text/x-gradle", false, 0.81},
		{[]string{".pom", "pom.xml"}, "maven", FamilyConfig, []string{}, []string{"<project ", "<groupId>", "<artifactId>", "<dependencies>"}, "text/x-maven", false, 0.78},

		// ===== HARDWARE & LOW-LEVEL =====
		{[]string{".s", ".asm", ".nasm", ".masm", ".inc"}, "assembly", FamilyHardware, []string{}, []string{"mov ", "add ", "sub ", "jmp ", "call ", "ret ", "push ", "pop "}, "text/x-asm", true, 0.60},
		{[]string{".ll"}, "llvm", FamilyHardware, []string{}, []string{"define ", "declare ", "alloca", "ret ", "br ", "phi"}, "text/x-llvm", false, 0.65},
		{[]string{".wat"}, "wast", FamilyWeb, []string{}, []string{"(module", "(func", "(memory", "(export", "(import"}, "text/x-wat", false, 0.85},
		{[]string{".v"}, "verilog", FamilyHardware, []string{}, []string{"module ", "input ", "output ", "always", "assign", "wire"}, "text/x-verilog", false, 0.72},
		{[]string{".vhd", ".vhdl"}, "vhdl", FamilyHardware, []string{}, []string{"entity ", "architecture ", "port(", "signal ", "process"}, "text/x-vhdl", false, 0.71},
		{[]string{".sv"}, "systemverilog", FamilyHardware, []string{}, []string{"module ", "interface ", "program ", "class ", "logic"}, "text/x-systemverilog", false, 0.73},
		{[]string{".sp", ".cir"}, "spice", FamilyHardware, []string{}, []string{".SUBCKT", ".MODEL", "VIN", ".END", "R", "C", "L"}, "text/x-spice", false, 0.58},

		// ===== SPECIAL FILES (no extension) =====
		{[]string{}, "dockerfile", FamilyConfig, []string{}, []string{"FROM ", "RUN ", "COPY ", "CMD"}, "text/x-dockerfile", true, 0.88},
		{[]string{}, "makefile", FamilyConfig, []string{}, []string{"all:", "clean:", ".PHONY:"}, "text/x-makefile", false, 0.82},
		{[]string{}, "cmake", FamilyConfig, []string{}, []string{"cmake_minimum_required", "project("}, "text/x-cmake", false, 0.79},
		{[]string{}, "ruby", FamilyScripting, []string{}, []string{"#!/usr/bin/env ruby", "def ", "class "}, "text/x-ruby", true, 0.88},
		{[]string{}, "python", FamilyScripting, []string{"python", "python3"}, []string{"#!/usr/bin/env python", "def ", "class "}, "text/x-python", true, 1.0},
		{[]string{}, "shell", FamilyScripting, []string{"bash", "sh", "zsh"}, []string{"#!/bin/", "export ", "echo "}, "text/x-shellscript", true, 0.90},
	}

	lc.mu.Lock()
	defer lc.mu.Unlock()

	for _, entry := range catalog {
		// Index by language
		lc.byLanguage[entry.Language] = entry
		lc.byFamily[entry.Family] = append(lc.byFamily[entry.Family], entry.Language)

		// Index by extension (normalize to lowercase)
		for _, ext := range entry.Extensions {
			normExt := strings.ToLower(ext)
			if !strings.HasPrefix(normExt, ".") {
				normExt = "." + normExt
			}
			lc.byExtension[normExt] = entry
			lc.stats.TotalExtensions++
		}

		// Index by MIME type
		if entry.MimeType != "" {
			lc.byMimeType[entry.MimeType] = entry
		}

		// Track Tree-Sitter availability
		if entry.TreeSitter {
			lc.stats.TreeSitterCount++
		}

		// Track average ARKHE compatibility
		lc.stats.AvgArkheScore += entry.ArkheScore
	}

	lc.stats.TotalLanguages = len(lc.byLanguage)
	if lc.stats.TotalLanguages > 0 {
		lc.stats.AvgArkheScore /= float64(lc.stats.TotalLanguages)
	}
}

// LookupByExtension retorna entrada por extensão de arquivo
func (lc *LanguageCatalog) LookupByExtension(ext string) *ExtensionEntry {
    lc.mu.RLock()
    defer lc.mu.RUnlock()

    normExt := strings.ToLower(ext)
    if !strings.HasPrefix(normExt, ".") {
        normExt = "." + normExt
    }
    return lc.byExtension[normExt]
	lc.mu.RLock()
	defer lc.mu.RUnlock()

	normExt := strings.ToLower(ext)
	if !strings.HasPrefix(normExt, ".") {
		normExt = "." + normExt
	}
	return lc.byExtension[normExt]
}

// LookupByLanguage retorna entrada por nome de linguagem
func (lc *LanguageCatalog) LookupByLanguage(lang string) *ExtensionEntry {
    lc.mu.RLock()
    defer lc.mu.RUnlock()
    return lc.byLanguage[strings.ToLower(lang)]
	lc.mu.RLock()
	defer lc.mu.RUnlock()
	return lc.byLanguage[strings.ToLower(lang)]
}

// LookupBySpecialFile retorna entrada para arquivos especiais sem extensão
func (lc *LanguageCatalog) LookupBySpecialFile(filename string) *ExtensionEntry {
    lc.mu.RLock()
    defer lc.mu.RUnlock()

    specialFiles := map[string]string{
        "Dockerfile": "dockerfile",
        "Makefile": "makefile",
        "CMakeLists.txt": "cmake",
        "Vagrantfile": "ruby",
        "Rakefile": "ruby",
        "Gemfile": "ruby",
        "Procfile": "yaml",
        ".bashrc": "shell",
        ".zshrc": "shell",
        ".vimrc": "vim",
        ".gitignore": "gitignore",
        "LICENSE": "text",
        "README": "markdown",
        "CHANGELOG": "markdown",
        "CONTRIBUTING": "markdown",
    }

    if lang, ok := specialFiles[filename]; ok {
        return lc.byLanguage[lang]
    }
    return nil
	lc.mu.RLock()
	defer lc.mu.RUnlock()

	specialFiles := map[string]string{
		"Dockerfile":     "dockerfile",
		"Makefile":       "makefile",
		"CMakeLists.txt": "cmake",
		"Vagrantfile":    "ruby",
		"Rakefile":       "ruby",
		"Gemfile":        "ruby",
		"Procfile":       "yaml",
		".bashrc":        "shell",
		".zshrc":         "shell",
		".vimrc":         "vim",
		".gitignore":     "gitignore",
		"LICENSE":        "text",
		"README":         "markdown",
		"CHANGELOG":      "markdown",
		"CONTRIBUTING":   "markdown",
	}

	if lang, ok := specialFiles[filename]; ok {
		return lc.byLanguage[lang]
	}
	return nil
}

// GetStats retorna estatísticas do catálogo
func (lc *LanguageCatalog) GetStats() CatalogStats {
    lc.mu.RLock()
    defer lc.mu.RUnlock()
    return lc.stats
	lc.mu.RLock()
	defer lc.mu.RUnlock()
	return lc.stats
}

// GetLanguagesByFamily retorna linguagens por família
func (lc *LanguageCatalog) GetLanguagesByFamily(family LanguageFamily) []string {
    lc.mu.RLock()
    defer lc.mu.RUnlock()
    return lc.byFamily[family]
	lc.mu.RLock()
	defer lc.mu.RUnlock()
	return lc.byFamily[family]
}

// GetAllLanguages retorna todas as linguagens conhecidas
func (lc *LanguageCatalog) GetAllLanguages() []string {
    lc.mu.RLock()
    defer lc.mu.RUnlock()

    langs := make([]string, 0, len(lc.byLanguage))
    for lang := range lc.byLanguage {
        langs = append(langs, lang)
    }
    return langs
	lc.mu.RLock()
	defer lc.mu.RUnlock()

	langs := make([]string, 0, len(lc.byLanguage))
	for lang := range lc.byLanguage {
		langs = append(langs, lang)
	}
	return langs
}
