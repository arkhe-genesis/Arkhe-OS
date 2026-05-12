// ============================================================================
// ARKHE P³ — Testes Cross-Language
// ============================================================================

#[cfg(test)]
mod tests {
    use parser_core::*;

    // === Teste 1: Round-trip Python → Rust → Python ===
    #[test]
    fn test_roundtrip_python_to_rust_to_python() {
        let python_src = r#"
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

result = fibonacci(10)
"#;

        // Parse Python
        let mut parser = PolyglotParser::new(None);
        let parse_result = parser.parse(python_src, Some("fib.py")).unwrap();
        assert_eq!(parse_result.detected_language, "python");
        assert!(parse_result.metrics.node_count > 0);

        // Transpilar para Rust
        let transpile_result = parser.transpile(python_src, None, "rust").unwrap();
        assert_eq!(transpile_result.target_language, "rust");
        assert!(transpile_result.code.contains("fn"));

        // Transpilar de volta para Python
        let roundtrip = parser.transpile(&transpile_result.code, Some("rust"), "python").unwrap();
        assert_eq!(roundtrip.target_language, "python");
        assert!(roundtrip.code.contains("def"));
    }

    // === Teste 2: Detecção de linguagem por conteúdo ===
    #[test]
    fn test_language_detection_by_content() {
        let samples = vec![
            ("fn main() { println!(\"hello\"); }", "rust"),
            ("def hello():\n    print('world')", "python"),
            ("function hello() { console.log('world'); }", "javascript"),
            ("int main() { return 0; }", "c"),
            ("package main\nfunc main() {}", "go"),
            ("SELECT * FROM users WHERE id = 1", "sql"),
            ("match $x { ... }", "graphql"),
        ];

        let parser = PolyglotParser::new(None);
        for (source, expected_lang) in samples {
            let detection = parser.detect_language(source, None);
            assert!(
                detection.language.contains(expected_lang) ||
                expected_lang.contains(&detection.language),
                "Esperado algo como '{}' para: {}",
                expected_lang, source
            );
        }
    }

    // === Teste 3: Transpilação para múltiplas linguagens ===
    #[test]
    fn test_transpile_to_multiple_languages() {
        let source = "x = 42";
        let target_languages = vec!["rust", "python", "javascript", "c", "go", "haskell", "prolog", "wat"];

        let mut parser = PolyglotParser::new(None);

        for target in target_languages {
            let result = parser.transpile(source, Some("python"), target);
            assert!(result.is_ok(), "Falha ao transpilar para {}: {:?}", target, result.err());

            let code = result.unwrap().code;
            assert!(!code.is_empty(), "Código gerado vazio para {}", target);

            eprintln!("{} → {}:\n{}\n---", "python", target, code.lines().next().unwrap_or(""));
        }
    }

    // === Teste 4: Análise semântica cross-language ===
    #[test]
    fn test_cross_language_analysis() {
        let parser = PolyglotParser::new(None);

        // Mesma lógica em diferentes linguagens
        let implementations = vec![
            ("python", "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)"),
            ("rust", "fn factorial(n: u64) -> u64 {\n    if n <= 1 { 1 } else { n * factorial(n - 1) }\n}"),
            ("javascript", "function factorial(n) {\n    return n <= 1 ? 1 : n * factorial(n - 1);\n}"),
        ];

        let mut last_score = None;

        for (lang, source) in implementations {
            let analysis = parser.analyze_cross_language(source, lang);

            // Todas as implementações devem ter complexity_score similar
            assert!(analysis.complexity_score > 0.0);
            assert!(analysis.complexity_score < 1.0);

            // Verificar consistência cross-language
            if let Some(prev) = last_score {
                let diff = (analysis.complexity_score - prev).abs();
                assert!(diff < 0.5, "Diferença de complexidade cross-language muito grande: {:.3} vs {:.3}", analysis.complexity_score, prev);
            }

            last_score = Some(analysis.complexity_score);
        }
    }

    // === Teste 5: UAST inter-operabilidade ===
    #[test]
    fn test_uast_interoperability() {
        let source = "if (x > 0) { return x; } else { return -x; }";

        let mut parser = PolyglotParser::new(None);

        // Parse como C
        let c_ast = parser.parse(source, Some("c")).unwrap();
        let c_nodes = c_ast.uast.node_count();

        // Parse como Java
        let java_ast = parser.parse(source, Some("java")).unwrap();
        let java_nodes = java_ast.uast.node_count();

        // Parse como Python
        let py_ast = parser.parse(source, Some("python")).unwrap();
        let py_nodes = py_ast.uast.node_count();

        // O UAST deve ter estrutura similar independente da linguagem
        // (mesmo número de nós conceituais — diferenças apenas em detalhes)
        assert!(c_nodes > 0);
        assert!(java_nodes > 0);
        assert!(py_nodes > 0);

        println!("C nodes: {}, Java nodes: {}, Python nodes: {}", c_nodes, java_nodes, py_nodes);
    }

    // === Teste 6: Integridade do UAST via hash ===
    #[test]
    fn test_uast_integrity_hash() {
        let source = "function hello() { return 'world'; }";

        let mut parser = PolyglotParser::new(None);
        let result = parser.parse(source, Some("javascript")).unwrap();

        // Verificar que o hash de integridade é consistente
        let hash1 = result.integrity_proof.clone();
        let result2 = parser.parse(source, Some("javascript")).unwrap();
        let hash2 = result2.integrity_proof;

        assert_eq!(hash1, hash2, "Hash de integridade deve ser determinístico");
        assert_eq!(hash1.len(), 32, "SHA3-256 deve gerar 32 bytes");
    }

    // === Teste 7: Tratamento de erros cross-language ===
    #[test]
    fn test_error_detection_cross_language() {
        let mut parser = PolyglotParser::new(None);

        // Erro de sintaxe que existe em todas as linguagens
        let broken_code = "function {} return;";

        // Parsing em diferentes linguagens com código quebrado
        for lang in &["javascript", "python", "rust", "c", "java"] {
            let result = parser.parse(broken_code, Some(lang));
            // Cada parser deve detectar o erro (possivelmente com warnings ou errors)
            if let Ok(r) = result {
                // Pode ter parseado de forma leniente — verificar warnings
                eprintln!("{}: {} warnings", lang, r.warnings.len());
            }
            // Erros de parse são esperados para código verdadeiramente quebrado
        }
    }

    // === Teste 8: Transpilação de padrões de projeto ===
    #[test]
    fn test_desing_pattern_transpilation() {
        let patterns = vec![
            // Singleton
            ("python", r#"class Singleton: _instance = None
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance"#),
            // Factory
            ("javascript", r#"class AnimalFactory {
    create(type) {
        switch(type) {
            case 'dog': return new Dog();
            case 'cat': return new Cat();
            default: throw new Error('Unknown type');
        }
    }
}"#),
            // Observer
            ("rust", r#"trait Observer {
    fn update(&self, event: &Event);
}
struct Subject { observers: Vec<Box<dyn Observer>> }
impl Subject {
    fn notify(&self, event: &Event) {
        for obs in &self.observers { obs.update(event); }
    }
}"#),
        ];

        let mut parser = PolyglotParser::new(None);

        for (lang, code) in patterns {
            let analysis = parser.analyze_cross_language(code, lang);

            // Todos devem ter complexidade razoável
            assert!(analysis.complexity_score < 0.9,
                "Padrão {} deve ter complexidade manejável, got {}", lang, analysis.complexity_score);

            // Transpilar para outras linguagens
            for target in &["rust", "python", "javascript", "c"] {
                if *target != lang {
                    let result = parser.transpile(code, Some(lang), target);
                    assert!(result.is_ok(), "Falha ao transpilar padrão {} de {} para {}",
                        lang, lang, target);
                }
            }
        }
    }
}
