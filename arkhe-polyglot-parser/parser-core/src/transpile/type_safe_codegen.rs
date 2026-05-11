// ============================================================================
// ARKHE P³ — Type-Safe Code Generation with Hindley-Milner Inference
// ============================================================================
// Integra inferência de tipos polimórfica ao CodeGen para garantir
// que transpilações preservem tipos entre linguagens.
// ============================================================================

use crate::ast::uast::{UAST, UASTNode, NodeId, NodeKind, TypeRef, AttributeValue};
use crate::semantic::{TypeEnvironment, TypeConstraint, TypeInferencer, SemanticInfo};
use std::collections::{HashMap, HashSet};

/// CodeGen com inferência de tipos integrada
pub struct TypeSafeCodeGen {
    target_language: String,
    inferencer: TypeInferencer,
    type_mappings: HashMap<String, TypeMapping>,
}

#[derive(Clone, Debug)]
pub struct TypeMapping {
    pub source_type: String,      // Tipo na linguagem fonte
    pub target_type: String,      // Tipo equivalente na linguagem alvo
    pub conversion_code: String,  // Código para conversão (se necessário)
    pub is_lossy: bool,           // Se a conversão pode perder informação
}

#[derive(Debug, thiserror::Error)]
pub enum TranspileError {
    #[error("Type Error: {0}")]
    TypeError(String),
    #[error("Unsupported Language: {0}")]
    UnsupportedLanguage(String),
}

impl TypeSafeCodeGen {
    pub fn new(target_language: &str) -> Self {
        Self {
            target_language: target_language.to_string(),
            inferencer: TypeInferencer::new(),
            type_mappings: Self::default_type_mappings(target_language),
        }
    }

    /// Gera código com verificação de tipos
    pub fn generate_typed(&mut self, uast: &mut UAST) -> Result<String, TranspileError> {
        // 1. Inferir tipos para toda a UAST
        self.inferencer.infer_types(uast)
            .map_err(|e| TranspileError::TypeError(e.to_string()))?;

        // 2. Gerar código com tipos resolvidos
        self.generate_with_types(uast)
    }

    fn generate_with_types(&self, uast: &UAST) -> Result<String, TranspileError> {
        match self.target_language.as_str() {
            "rust" => self.generate_rust_typed(uast),
            _ => Err(TranspileError::UnsupportedLanguage(
                self.target_language.clone())),
        }
    }

    fn generate_rust_typed(&self, uast: &UAST) -> Result<String, TranspileError> {
        let mut output = String::new();
        output.push_str("// Transpilado pelo ARKHE P³ com inferência de tipos\n");

        // Gerar imports baseados nos tipos usados
        let used_types = self.collect_used_types(uast);
        if used_types.contains("Vec") {
            output.push_str("use std::vec::Vec;\n");
        }
        if used_types.contains("Option") {
            output.push_str("use std::option::Option;\n");
        }
        output.push('\n');

        // Gerar declarações com tipos inferidos
        for node in uast.nodes.values() {
            if node.kind == NodeKind::DeclTypeAlias {
                let name = node.attributes.get("name")
                    .and_then(|v| match v { AttributeValue::String(s) => Some(s.clone()), _ => None })
                    .unwrap_or_else(|| "Alias".to_string());

                let target_type = if let Some(ref si) = node.semantic_info {
                    if let Some(ref tr) = si.type_info {
                        self.map_type_to_rust(tr)
                    } else {
                        "()".to_string()
                    }
                } else {
                    "()".to_string()
                };

                output.push_str(&format!("type {} = {};\n", name, target_type));
                continue;
            }

            if node.kind == NodeKind::DeclTrait {
                let name = node.attributes.get("name")
                    .and_then(|v| match v { AttributeValue::String(s) => Some(s.clone()), _ => None })
                    .unwrap_or_else(|| "Trait".to_string());
                output.push_str(&format!("trait {} {{\n    // members\n}}\n", name));
                continue;
            }

            if let Some(type_info) = &node.semantic_info {
                if let Some(ref type_ref) = type_info.type_info {
                    match &node.kind {
                        NodeKind::DeclVariable => {
                            let default_name = "x".to_string();
                            let name = node.attributes.get("name")
                                .and_then(|v| match v { AttributeValue::String(s) => Some(s), _ => None })
                                .unwrap_or(&default_name);
                            let rust_type = self.map_type_to_rust(type_ref);
                            output.push_str(&format!("let {}: {} = ", name, rust_type));
                            // Gerar expressão de inicialização...
                            output.push_str("/* value */;\n");
                        }
                        NodeKind::DeclFunction => {
                            output.push_str(&self.gen_function_signature_rust(uast, node, type_info)?);
                        }
                        _ => {}
                    }
                }
            }
        }

        Ok(output)
    }

    fn gen_function_signature_rust(
        &self,
        uast: &UAST,
        node: &UASTNode,
        type_info: &crate::semantic::SemanticInfo,
    ) -> Result<String, TranspileError> {
        let default_fn_name = "fn".to_string();
        let name = node.attributes.get("name")
            .and_then(|v| match v { AttributeValue::String(s) => Some(s), _ => None })
            .unwrap_or(&default_fn_name);

        // Parâmetros com tipos
        let params_res: Result<Vec<String>, _> = node.children.iter()
            .filter_map(|child_id| uast.nodes.get(child_id))
            .filter(|n| matches!(n.kind, NodeKind::DeclVariable))
            .map(|param_node| {
                if let Some(ref si) = param_node.semantic_info {
                    if let Some(ref tr) = si.type_info {
                        let default_arg = "arg".to_string();
                        let param_name = param_node.attributes.get("name")
                            .and_then(|v| match v { AttributeValue::String(s) => Some(s), _ => None })
                            .unwrap_or(&default_arg);
                        let rust_type = self.map_type_to_rust(tr);
                        Ok(format!("{}: {}", param_name, rust_type))
                    } else {
                        let default_unknown = "unknown".to_string();
                        Err(TranspileError::TypeError(
                            format!("Parameter {} has no type",
                                param_node.attributes.get("name")
                                    .and_then(|v| match v { AttributeValue::String(s) => Some(s), _ => None })
                                    .unwrap_or(&default_unknown))))
                    }
                } else {
                    Ok("arg: /* unknown */".to_string())
                }
            })
            .collect();

        let params = params_res?;

        // Tipo de retorno
        let return_type = if let Some(ref tr) = type_info.type_info {
            format!(" -> {}", self.map_type_to_rust(tr))
        } else {
            String::new()
        };

        Ok(format!("fn {}({}){} {{\n    // body\n}}\n",
            name, params.join(", "), return_type))
    }

    fn map_type_to_rust(&self, type_ref: &TypeRef) -> String {
        // Mapeamento canônico de tipos para Rust
        match type_ref.name.as_str() {
            "Int" | "i32" | "i64" => type_ref.name.clone(),
            "Float" | "f32" | "f64" => type_ref.name.clone(),
            "Bool" => "bool".to_string(),
            "String" => "String".to_string(),
            "List" => {
                if let Some(inner) = type_ref.generics.first() {
                    format!("Vec<{}>", self.map_type_to_rust(inner))
                } else {
                    "Vec</* unknown */>".to_string()
                }
            }
            "Option" => {
                if let Some(inner) = type_ref.generics.first() {
                    format!("Option<{}>", self.map_type_to_rust(inner))
                } else {
                    "Option</* unknown */>".to_string()
                }
            }
            "Tuple" => {
                let inner: Vec<String> = type_ref.generics.iter()
                    .map(|t| self.map_type_to_rust(t))
                    .collect();
                format!("({})", inner.join(", "))
            }
            _ => type_ref.name.clone(), // Fallback
        }
    }

    fn collect_used_types(&self, uast: &UAST) -> HashSet<String> {
        let mut types = HashSet::new();
        for node in uast.nodes.values() {
            if let Some(ref si) = node.semantic_info {
                if let Some(ref tr) = si.type_info {
                    self.collect_type_names(tr, &mut types);
                }
            }
        }
        types
    }

    fn collect_type_names(&self, type_ref: &TypeRef, types: &mut HashSet<String>) {
        types.insert(type_ref.name.clone());
        for generic in &type_ref.generics {
            self.collect_type_names(generic, types);
        }
    }

    fn default_type_mappings(target: &str) -> HashMap<String, TypeMapping> {
        let mut mappings = HashMap::new();
        // Exemplo para Rust
        if target == "rust" {
            mappings.insert("Int".to_string(), TypeMapping {
                source_type: "Int".to_string(),
                target_type: "i64".to_string(),
                conversion_code: "as i64".to_string(),
                is_lossy: false,
            });
            mappings.insert("String".to_string(), TypeMapping {
                source_type: "String".to_string(),
                target_type: "String".to_string(),
                conversion_code: ".to_string()".to_string(),
                is_lossy: false,
            });
            // ... mais mapeamentos
        }
        mappings
    }
}
