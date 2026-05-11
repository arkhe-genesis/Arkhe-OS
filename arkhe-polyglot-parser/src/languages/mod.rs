// ============================================================================
// ARKHE P³ — Language Registry
// ============================================================================
// Registro central de todas as linguagens suportadas pelo P³.
// Cada linguagem é um módulo com gramática, lexer e semântica.
// ============================================================================

use crate::grammar::{Grammar, LanguageType, ProductionRule, Symbol, TerminalDefinition, TerminalFlags};
use ahash::AHashMap;

/// Registro global de linguagens
pub struct LanguageRegistry {
    languages: AHashMap<String, LanguageSpec>,
    total_languages: usize,
}

#[derive(Clone, Debug)]
pub struct LanguageSpec {
    pub name: String,
    pub display_name: String,
    pub version: String,
    pub language_type: LanguageType,
    pub author: String,
    pub description: String,
    pub file_extensions: Vec<String>,
    pub shebangs: Vec<String>,
    pub grammar_version: String,
}

impl LanguageRegistry {
    pub fn new() -> Self {
        Self {
            languages: AHashMap::new(),
            total_languages: 0,
        }
    }

    /// Registrar linguagem padrão
    pub fn register_defaults(&mut self) {
        // ===== LINGUAGENS DE PROGRAMAÇÃO =====

        // --- Rust ---
        self.register(LanguageSpec {
            name: "rust".to_string(),
            display_name: "Rust".to_string(),
            version: "2024".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Mozilla Foundation / Rust Team".to_string(),
            description: "Systems programming language focused on safety, speed, and concurrency.".to_string(),
            file_extensions: vec![".rs".into()],
            shebangs: vec!["#!/usr/bin/env rust".into()],
            grammar_version: "1.0.0".to_string(),
        }).unwrap();

        // --- Python ---
        self.register(LanguageSpec {
            name: "python".to_string(),
            display_name: "Python".to_string(),
            version: "3.12".to_string(),
            language_type: LanguageType::IndentationSensitive,
            author: "Guido van Rossum / Python Software Foundation".to_string(),
            description: "High-level interpreted language emphasizing readability and simplicity.".to_string(),
            file_extensions: vec![".py".into(), ".pyw".into(), ".pyi".into()],
            shebangs: vec!["#!/usr/bin/env python3".into()],
            grammar_version: "3.12.0".to_string(),
        }).unwrap();

        // --- JavaScript ---
        self.register(LanguageSpec {
            name: "javascript".to_string(),
            display_name: "JavaScript".to_string(),
            version: "ES2024".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Brendan Eich / ECMA International".to_string(),
            description: "Dynamic, interpreted language for web and server.".to_string(),
            file_extensions: vec![".js".into(), ".mjs".into(), ".cjs".into()],
            shebangs: vec!["#!/usr/bin/env node".into()],
            grammar_version: "ES2024".to_string(),
        }).unwrap();

        // --- TypeScript ---
        self.register(LanguageSpec {
            name: "typescript".to_string(),
            display_name: "TypeScript".to_string(),
            version: "5.4".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Microsoft".to_string(),
            description: "JavaScript with optional static typing.".to_string(),
            file_extensions: vec![".ts".into(), ".mts".into(), ".cts".into(), ".tsx".into()],
            shebangs: vec!["#!/usr/bin/env ts-node".into()],
            grammar_version: "5.4.0".to_string(),
        }).unwrap();

        // --- C ---
        self.register(LanguageSpec {
            name: "c".to_string(),
            display_name: "C".to_string(),
            version: "C17".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Dennis Ritchie / ISO/IEC".to_string(),
            description: "General-purpose procedural language.".to_string(),
            file_extensions: vec![".c".into(), ".h".into()],
            shebangs: Vec::new(),
            grammar_version: "C17".to_string(),
        }).unwrap();

        // --- C++ ---
        self.register(LanguageSpec {
            name: "cpp".to_string(),
            display_name: "C++".to_string(),
            version: "C++23".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Bjarne Stroustrup / ISO/IEC".to_string(),
            description: "Multi-paradigm language with OOP, templates, and systems features.".to_string(),
            file_extensions: vec![".cpp".into(), ".cc".into(), ".cxx".into(), ".hpp".into(), ".h".into()],
            shebangs: Vec::new(),
            grammar_version: "C++23".to_string(),
        }).unwrap();

        // --- Go ---
        self.register(LanguageSpec {
            name: "go".to_string(),
            display_name: "Go".to_string(),
            version: "1.21".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Google (Rob Pike, Ken Thompson, Robert Griesemer)".to_string(),
            description: "Simple, fast, concurrent programming language.".to_string(),
            file_extensions: vec![".go".into()],
            shebangs: vec!["#!/usr/bin/env go run".into()],
            grammar_version: "1.21.0".to_string(),
        }).unwrap();

        // --- Zig ---
        self.register(LanguageSpec {
            name: "zig".to_string(),
            display_name: "Zig".to_string(),
            version: "0.12".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Andrew Kelley".to_string(),
            description: "General-purpose language for robust, optimal software.".to_string(),
            file_extensions: vec![".zig".into()],
            shebangs: Vec::new(),
            grammar_version: "0.12.0".to_string(),
        }).unwrap();

        // --- V ---
        self.register(LanguageSpec {
            name: "v".to_string(),
            display_name: "V".to_string(),
            version: "0.4".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Alexander Medvednikov".to_string(),
            description: "Simple, fast, safe language for writing maintainable software.".to_string(),
            file_extensions: vec![".v".into(), ".vs".into()],
            shebangs: Vec::new(),
            grammar_version: "0.4.0".to_string(),
        }).unwrap();

        // --- Crystal ---
        self.register(LanguageSpec {
            name: "crystal".to_string(),
            display_name: "Crystal".to_string(),
            version: "1.11".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Ary Borenszweig / Manas Technology Solutions".to_string(),
            description: "Language with Ruby-like syntax and C-like performance.".to_string(),
            file_extensions: vec![".cr".into()],
            shebangs: vec!["#!/usr/bin/env crystal".into()],
            grammar_version: "1.11.0".to_string(),
        }).unwrap();

        // --- Nim ---
        self.register(LanguageSpec {
            name: "nim".to_string(),
            display_name: "Nim".to_string(),
            version: "2.0".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Andreas Rumpf".to_string(),
            description: "Statically typed compiled language with Python-like syntax.".to_string(),
            file_extensions: vec![".nim".into()],
            shebangs: vec!["#!/usr/bin/env nim".into()],
            grammar_version: "2.0.0".to_string(),
        }).unwrap();

        // --- Kotlin ---
        self.register(LanguageSpec {
            name: "kotlin".to_string(),
            display_name: "Kotlin".to_string(),
            version: "2.0".to_string(),
            language_type: LanguageType::FreeForm,
            author: "JetBrains".to_string(),
            description: "Modern multiplatform language for JVM, JS, and native.".to_string(),
            file_extensions: vec![".kt".into(), ".kts".into()],
            shebangs: Vec::new(),
            grammar_version: "2.0.0".to_string(),
        }).unwrap();

        // --- Haskell ---
        self.register(LanguageSpec {
            name: "haskell".to_string(),
            display_name: "Haskell".to_string(),
            version: "2010 / GHC 9.6".to_string(),
            language_type: LanguageType::Mixed,
            author: "Haskell Committee / Simon Peyton Jones".to_string(),
            description: "Purely functional language with lazy evaluation.".to_string(),
            file_extensions: vec![".hs".into()],
            shebangs: Vec::new(),
            grammar_version: "2010".to_string(),
        }).unwrap();

        // --- OCaml ---
        self.register(LanguageSpec {
            name: "ocaml".to_string(),
            display_name: "OCaml".to_string(),
            version: "5.1".to_string(),
            language_type: LanguageType::FreeForm,
            author: "INRIA".to_string(),
            description: "Functional, imperative, and object-oriented language.".to_string(),
            file_extensions: vec![".ml".into(), ".mli".into()],
            shebangs: Vec::new(),
            grammar_version: "5.1.0".to_string(),
        }).unwrap();

        // --- F# ---
        self.register(LanguageSpec {
            name: "fsharp".to_string(),
            display_name: "F#".to_string(),
            version: "8.0".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Don Syme / Microsoft".to_string(),
            description: "Functional-first language for .NET.".to_string(),
            file_extensions: vec![".fs".into(), ".fsx".into()],
            shebangs: Vec::new(),
            grammar_version: "8.0.0".to_string(),
        }).unwrap();

        // ===== LINGUAGENS DE LÓGICA =====

        // --- Prolog ---
        self.register(LanguageSpec {
            name: "prolog".to_string(),
            display_name: "Prolog".to_string(),
            version: "ISO".to_string(),
            language_type: LanguageType::PatternBased,
            author: "Alain Colmerauer / Robert Kowalski".to_string(),
            description: "Logic programming language for AI and theorem proving.".to_string(),
            file_extensions: vec![".pl".into(), ".pro".into(), ".lp".into()],
            shebangs: vec!["#!/usr/bin/env swipl".into()],
            grammar_version: "ISO".to_string(),
        }).unwrap();

        // --- Mercury ---
        self.register(LanguageSpec {
            name: "mercury".to_string(),
            display_name: "Mercury".to_string(),
            version: "22.01".to_string(),
            language_type: LanguageType::PatternBased,
            author: "Zoltan Somogyi et al.".to_string(),
            description: "Logic-functional language with strong type system.".to_string(),
            file_extensions: vec![".m".into()],
            shebangs: Vec::new(),
            grammar_version: "22.01".to_string(),
        }).unwrap();

        // --- Datalog ---
        self.register(LanguageSpec {
            name: "datalog".to_string(),
            display_name: "Datalog".to_string(),
            version: "Soufflé".to_string(),
            language_type: LanguageType::PatternBased,
            author: "Various / Soufflé project".to_string(),
            description: "Declarative logic language for deductive databases.".to_string(),
            file_extensions: vec![".dl".into(), ".facts".into()],
            shebangs: Vec::new(),
            grammar_version: "Soufflé".to_string(),
        }).unwrap();

        // ===== LINGUAGENS DE CONSULTA =====

        // --- SQL ---
        self.register(LanguageSpec {
            name: "sql".to_string(),
            display_name: "SQL".to_string(),
            version: "SQL:2023".to_string(),
            language_type: LanguageType::Declarative,
            author: "Donald Chamberlin / Raymond Boyce / ISO".to_string(),
            description: "Query language for relational databases.".to_string(),
            file_extensions: vec![".sql".into()],
            shebangs: Vec::new(),
            grammar_version: "SQL:2023".to_string(),
        }).unwrap();

        // --- Cypher ---
        self.register(LanguageSpec {
            name: "cypher".to_string(),
            display_name: "Cypher".to_string(),
            version: "GQL / Neo4j 5".to_string(),
            language_type: LanguageType::Declarative,
            author: "Andrés Taylor / Neo4j".to_string(),
            description: "Graph query language for property graphs.".to_string(),
            file_extensions: vec![".cypher".into()],
            shebangs: Vec::new(),
            grammar_version: "GQL".to_string(),
        }).unwrap();

        // --- SPARQL ---
        self.register(LanguageSpec {
            name: "sparql".to_string(),
            display_name: "SPARQL".to_string(),
            version: "1.2".to_string(),
            language_type: LanguageType::Declarative,
            author: "W3C RDF Data Access Working Group".to_string(),
            description: "Query language for RDF graphs.".to_string(),
            file_extensions: vec![".rq".into(), ".sparql".into()],
            shebangs: Vec::new(),
            grammar_version: "1.2".to_string(),
        }).unwrap();

        // --- Gremlin ---
        self.register(LanguageSpec {
            name: "gremlin".to_string(),
            display_name: "Gremlin".to_string(),
            version: "3.7".to_string(),
            language_type: LanguageType::PatternBased,
            author: "Apache TinkerPop".to_string(),
            description: "Graph traversal language for Apache TinkerPop.".to_string(),
            file_extensions: vec![".gremlin".into()],
            shebangs: Vec::new(),
            grammar_version: "3.7".to_string(),
        }).unwrap();

        // ===== LINGUAGENS DE BLOCKCHAIN / WEB3 =====

        // --- Cairo ---
        self.register(LanguageSpec {
            name: "cairo".to_string(),
            display_name: "Cairo".to_string(),
            version: "2.7".to_string(),
            language_type: LanguageType::FreeForm,
            author: "StarkWare Industries".to_string(),
            description: "Language for writing provable programs on StarkNet.".to_string(),
            file_extensions: vec![".cairo".into()],
            shebangs: Vec::new(),
            grammar_version: "2.7".to_string(),
        }).unwrap();

        // --- Noir ---
        self.register(LanguageSpec {
            name: "noir".to_string(),
            display_name: "Noir".to_string(),
            version: "0.1".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Aztec Network".to_string(),
            description: "Language for writing private smart contracts.".to_string(),
            file_extensions: vec![".nr".into()],
            shebangs: Vec::new(),
            grammar_version: "0.1".to_string(),
        }).unwrap();

        // --- Move ---
        self.register(LanguageSpec {
            name: "move".to_string(),
            display_name: "Move".to_string(),
            version: "1.0".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Meta (Diem Association) / Aptos / Sui".to_string(),
            description: "Safe smart contract language for blockchain.".to_string(),
            file_extensions: vec![".move".into()],
            shebangs: Vec::new(),
            grammar_version: "1.0".to_string(),
        }).unwrap();

        // --- Solidity ---
        self.register(LanguageSpec {
            name: "solidity".to_string(),
            display_name: "Solidity".to_string(),
            version: "0.8.24".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Gavin Wood / Ethereum Foundation".to_string(),
            description: "Smart contract language for Ethereum.".to_string(),
            file_extensions: vec![".sol".into()],
            shebangs: Vec::new(),
            grammar_version: "0.8.24".to_string(),
        }).unwrap();

        // ===== LINGUAGENS DE CONTRATO INTELIGENTE / FORMAL =====

        // --- Coq ---
        self.register(LanguageSpec {
            name: "coq".to_string(),
            display_name: "Coq".to_string(),
            version: "8.19".to_string(),
            language_type: LanguageType::PatternBased,
            author: "INRIA / Gallina Team".to_string(),
            description: "Formal proof management system.".to_string(),
            file_extensions: vec![".v".into()],
            shebangs: Vec::new(),
            grammar_version: "8.19".to_string(),
        }).unwrap();

        // --- Agda ---
        self.register(LanguageSpec {
            name: "agda".to_string(),
            display_name: "Agda".to_string(),
            version: "2.6.3".to_string(),
            language_type: LanguageType::Mixed,
            author: "Ulf Norell / Chalmers University".to_string(),
            description: "Dependently typed functional programming language.".to_string(),
            file_extensions: vec![".agda".into()],
            shebangs: Vec::new(),
            grammar_version: "2.6.3".to_string(),
        }).unwrap();

        // --- Idris ---
        self.register(LanguageSpec {
            name: "idris".to_string(),
            display_name: "Idris".to_string(),
            version: "2".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Edwin Brady".to_string(),
            description: "General purpose dependently typed language.".to_string(),
            file_extensions: vec![".idr".into()],
            shebangs: Vec::new(),
            grammar_version: "2.0".to_string(),
        }).unwrap();

        // ===== LINGUAGENS DE SCRIPTING =====

        // --- Lua ---
        self.register(LanguageSpec {
            name: "lua".to_string(),
            display_name: "Lua".to_string(),
            version: "5.4".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Roberto Ierusalimschy / PUC-Rio".to_string(),
            description: "Lightweight embeddable scripting language.".to_string(),
            file_extensions: vec![".lua".into()],
            shebangs: vec!["#!/usr/bin/env lua".into()],
            grammar_version: "5.4".to_string(),
        }).unwrap();

        // --- Ruby ---
        self.register(LanguageSpec {
            name: "ruby".to_string(),
            display_name: "Ruby".to_string(),
            version: "3.3".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Yukihiro Matsumoto".to_string(),
            description: "Dynamic, reflective, object-oriented language.".to_string(),
            file_extensions: vec![".rb".into()],
            shebangs: vec!["#!/usr/bin/env ruby".into()],
            grammar_version: "3.3".to_string(),
        }).unwrap();

        // --- R ---
        self.register(LanguageSpec {
            name: "r".to_string(),
            display_name: "R".to_string(),
            version: "4.3".to_string(),
            language_type: LanguageType::ExpressionBased,
            author: "R Core Team".to_string(),
            description: "Language for statistical computing and graphics.".to_string(),
            file_extensions: vec![".r".into(), ".R".into()],
            shebangs: Vec::new(),
            grammar_version: "4.3".to_string(),
        }).unwrap();

        // --- Julia ---
        self.register(LanguageSpec {
            name: "julia".to_string(),
            display_name: "Julia".to_string(),
            version: "1.10".to_string(),
            language_type: LanguageType::FreeForm,
            author: "Jeff Bezanson / Stefan Karpinski / Viral B. Shah".to_string(),
            description: "High-level, high-performance language for technical computing.".to_string(),
            file_extensions: vec![".jl".into()],
            shebangs: vec!["#!/usr/bin/env julia".into()],
            grammar_version: "1.10".to_string(),
        }).unwrap();

        // ===== MARKUP / DATA FORMATS =====

        // --- WAT (WebAssembly Text) ---
        self.register(LanguageSpec {
            name: "wat".to_string(),
            display_name: "WebAssembly Text".to_string(),
            version: "1.0".to_string(),
            language_type: LanguageType::ExpressionBased,
            author: "W3C WebAssembly Working Group".to_string(),
            description: "Text format for WebAssembly binary format.".to_string(),
            file_extensions: vec![".wat".into()],
            shebangs: Vec::new(),
            grammar_version: "1.0".to_string(),
        }).unwrap();

        // --- YAML ---
        self.register(LanguageSpec {
            name: "yaml".to_string(),
            display_name: "YAML".to_string(),
            version: "1.2".to_string(),
            language_type: LanguageType::Declarative,
            author: "Clark C. Evans / Oren Ben-Kiki / Ingy döt Net".to_string(),
            description: "Human-readable data serialization format.".to_string(),
            file_extensions: vec![".yml".into(), ".yaml".into()],
            shebangs: Vec::new(),
            grammar_version: "1.2".to_string(),
        }).unwrap();

        // --- TOML ---
        self.register(LanguageSpec {
            name: "toml".to_string(),
            display_name: "TOML".to_string(),
            version: "1.0".to_string(),
            language_type: LanguageType::Declarative,
            author: "Tom Preston-Werner".to_string(),
            description: "Minimal configuration file format.".to_string(),
            file_extensions: vec![".toml".into()],
            shebangs: Vec::new(),
            grammar_version: "1.0".to_string(),
        }).unwrap();

        // ===== ARKHE-SPECIFIC =====

        // --- AGI Spec ---
        self.register(LanguageSpec {
            name: "agi".to_string(),
            display_name: "AGI Specification".to_string(),
            version: "1.0".to_string(),
            language_type: LanguageType::Declarative,
            author: "ARKHE Cathedral".to_string(),
            description: "ARKHE General Intelligence specification format.".to_string(),
            file_extensions: vec![".agi".into()],
            shebangs: Vec::new(),
            grammar_version: "1.0".to_string(),
        }).unwrap();

        // --- ARKHE Assembly ---
        self.register(LanguageSpec {
            name: "arkasm".to_string(),
            display_name: "ARKHE Assembly".to_string(),
            version: "1.0".to_string(),
            language_type: LanguageType::ExpressionBased,
            author: "ARKHE Cathedral".to_string(),
            description: "Low-level assembly for ARKHE Virtual Machine.".to_string(),
            file_extensions: vec![".arkasm".into()],
            shebangs: Vec::new(),
            grammar_version: "1.0".to_string(),
        }).unwrap();

        self.total_languages = self.languages.len();

        println!("[ARKHE P³] Registered {} languages", self.total_languages);
    }

    /// Registrar linguagem customizada
    pub fn register(&mut self, spec: LanguageSpec) -> Result<(), String> {
        let name = spec.name.clone();
        if self.languages.contains_key(&name) {
            return Err(format!("Language '{}' already registered", name));
        }

        // Validar
        if name.is_empty() {
            return Err("Language name cannot be empty".to_string());
        }
        if spec.file_extensions.is_empty() {
            return Err(format!("Language '{}' has no file extensions", name));
        }

        self.languages.insert(name, spec);
        self.total_languages += 1;
        Ok(())
    }

    /// Buscar linguagem por nome
    pub fn get(&self, name: &str) -> Option<&LanguageSpec> {
        // Exato
        if let Some(spec) = self.languages.get(name) {
            return Some(spec);
        }
        // Case-insensitive
        let lower = name.to_lowercase();
        self.languages.get(&lower)
    }

    /// Buscar por extensão de arquivo
    pub fn get_by_extension(&self, ext: &str) -> Option<&LanguageSpec> {
        let ext_lower = ext.to_lowercase();
        self.languages.values()
            .find(|spec| {
                spec.file_extensions.iter()
                    .any(|e| e.to_lowercase() == ext_lower)
            })
    }

    /// Buscar por shebang
    pub fn get_by_shebang(&self, line: &str) -> Option<&LanguageSpec> {
        self.languages.values()
            .find(|spec| {
                spec.shebangs.iter()
                    .any(|s| line.starts_with(s))
            })
    }

    /// Detectar linguagem por conteúdo e nome
    pub fn detect(
        &self,
        filename: Option<&str>,
        content: &str,
    ) -> Option<(&LanguageSpec, f64)> {
        let mut candidates = Vec::new();

        // 1. Por extensão
        if let Some(name) = filename {
            if let Some(ext) = std::path::Path::new(name).extension() {
                if let Some(spec) = self.get_by_extension(ext.to_str().unwrap_or("")) {
                    candidates.push((spec, 0.8));
                }
            }
        }

        // 2. Por shebang
        let first_line = content.lines().next().unwrap_or("");
        if let Some(spec) = self.get_by_shebang(first_line) {
            candidates.push((spec, 0.95));
        }

        // 3. Análise de conteúdo (keywords e padrões)
        for spec in self.languages.values() {
            let score = self.score_content_match(content, spec);
            if score > 0.3 {
                candidates.push((spec, score));
            }
        }

        // Retornar melhor candidato
        candidates
            .into_iter()
            .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
    }

    /// Score de correspondência entre conteúdo e linguagem
    fn score_content_match(&self, content: &str, spec: &LanguageSpec) -> f64 {
        // Analisar keywords específicas
        let keywords = self.get_keywords_for_language(&spec.name);
        let mut hits = 0;
        let mut total = keywords.len();

        for kw in &keywords {
            if content.contains(kw) {
                hits += 1;
            }
        }

        if total == 0 {
            return 0.0;
        }

        (hits as f64 / total as f64).min(1.0)
    }

    fn get_keywords_for_language(&self, lang: &str) -> Vec<&'static str> {
        match lang {
            "rust" => vec!["fn ", "let mut", "impl", "trait", "struct", "enum", "match", "pub fn", "use ", "mod ", "unsafe", "mut ", "dyn ", "where", "loop", "async fn", "await", "box ", "crate::", "self.", "&mut", "&self", "#[derive", "-> "],
            "python" => vec!["def ", "class ", "import ", "from ", "as ", "if ", "elif ", "else:", "for ", "while ", "try:", "except", "with ", "yield", "lambda", "return", "None", "True", "False", "raise", "pass", "self,", "print(", "f'", "f\""],
            "javascript" => vec!["function ", "const ", "let ", "var ", "=>", "async function", "await ", "export ", "import ", "class ", "extends", "new ", "typeof ", "instanceof", "document.", "console."],
            "typescript" => vec!["interface ", "type ", ": string", ": number", ": boolean", "as ", "enum ", "readonly", "generic", "extends ", "implements", "declare", "namespace", "Record<", "Partial<", "Pick<", "Omit<"],
            "c" => vec!["#include", "int main", "printf", "malloc", "free", "struct ", "typedef ", "char *", "void *", "for (", "while (", "#define", "return 0;"],
            "cpp" => vec!["#include", "int main", "namespace", "std::", "class ", "template", "public:", "private:", "virtual", "override", "->", "cout <<", "std::cout"],
            "go" => vec!["func ", "package ", "import ", "var ", "const ", "type ", "struct", "interface", "go ", "defer ", "chan ", "goroutine", "fmt.Println", "make(", "range "],
            "zig" => vec!["fn ", "const ", "var ", "pub fn", "comptime", "struct {", "union(enum)", "test ", "try ", "defer ", "errdefer", "usingnamespace"],
            "haskell" => vec!["module ", "where", "let", "in ", "case ", "of ", "do ", "data ", "type ", "class ", "instance", "import ", ":: ", "->", "= ", "where"],
            "prolog" => vec![":-", "?", "- ", "is ", "write(", "read(", "nl", "fail.", "true.", "assert", "retract", "atom"],
            "sql" => vec!["SELECT ", "FROM ", "WHERE ", "JOIN ", "ON ", "GROUP BY", "ORDER BY", "INSERT INTO", "UPDATE ", "DELETE FROM", "CREATE TABLE", "ALTER TABLE", "DISTINCT", "COUNT(", "SUM("],
            "cypher" => vec!["MATCH ", "CREATE ", "MERGE ", "WHERE ", "RETURN ", "WITH ", "DELETE ", "SET ", "REMOVE ", "UNWIND"],
            "sparql" => vec!["PREFIX ", "SELECT ", "WHERE {", "?s ", "?p ", "?o ", "FILTER", "ORDER BY", "LIMIT"],
            "cairo" => vec!["func ", "fn main", "@storage", "@event", "@interface", "returns", "felt", "uint256", "implicits", "builtins"],
            "noir" => vec!["fn ", "pub fn", "let ", "mut ", "for ", "in ", "comptime", "unconstrained", "std::"],
            "move" => vec!["module ", "fun ", "struct ", "resource ", "public ", "acquires", "native", "spec ", "invariant", "pragma"],
            "solidity" => vec!["pragma solidity", "contract ", "function ", "event ", "mapping(", "msg.sender", "require(", "emit ", "address", "uint256", "IERC"],
            "agi" => vec!["name:", "version:", "description:", "type:", "input:", "output:", "constraint:", "permission:", "endpoint:", "payload:", "signature:"],
            _ => vec![],
        }
    }

    /// Total de linguagens registradas
    pub fn count(&self) -> usize {
        self.total_languages
    }

    /// Listar todas as linguagens
    pub fn list_all(&self) -> Vec<String> {
        self.languages.keys().cloned().collect()
    }

    /// Listar linguagens por tipo
    pub fn list_by_type(&self, lang_type: LanguageType) -> Vec<&LanguageSpec> {
        self.languages.values()
            .filter(|s| s.language_type == lang_type)
            .collect()
    }
}
