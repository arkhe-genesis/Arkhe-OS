// ============================================================================
// ARKHE P³ — PlantUML Documentation Generator
// ============================================================================
// Gera diagramas PlantUML da estrutura UAST para documentação.
// PlantUML suporta: class diagrams, activity diagrams, sequence diagrams.
// ============================================================================

use crate::ast::uast::{UAST, UASTNode, NodeId, NodeKind, AttributeValue};
use std::collections::{HashMap, HashSet};

/// Gerador de documentação PlantUML
pub struct PlantUMLDocGenerator {
    max_depth: usize,
    show_types: bool,
    show_source_ranges: bool,
    diagram_type: PlantUMLType,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum PlantUMLType {
    ClassDiagram,      // Hierarquia de nós
    ActivityDiagram,   // Fluxo de controle
    SequenceDiagram,   // Chamadas entre funções
    Graphviz,          // Grafo DOT
}

impl PlantUMLDocGenerator {
    pub fn new(diagram_type: PlantUMLType) -> Self {
        Self {
            max_depth: 10,
            show_types: true,
            show_source_ranges: false,
            diagram_type,
        }
    }

    /// Gera diagrama PlantUML ou Graphviz da UAST
    pub fn to_plantuml(&self, uast: &UAST, title: Option<&str>) -> String {
        match self.diagram_type {
            PlantUMLType::ClassDiagram => self.to_class_diagram(uast, title),
            PlantUMLType::ActivityDiagram => self.to_activity_diagram(uast, title),
            PlantUMLType::SequenceDiagram => self.to_sequence_diagram(uast, title),
            PlantUMLType::Graphviz => self.to_graphviz(uast, title),
        }
    }

    fn to_graphviz(&self, uast: &UAST, title: Option<&str>) -> String {
        let mut output = String::new();
        output.push_str("digraph UAST {\n");
        if let Some(t) = title {
            output.push_str(&format!("  label=\"{}\";\n", t));
        }

        for node in uast.nodes.values() {
            let label = self.node_label_plantuml(node);
            output.push_str(&format!("  N{} [label=\"{}\"];\n", node.id.0, label));
            for child in &node.children {
                output.push_str(&format!("  N{} -> N{};\n", node.id.0, child.0));
            }
        }
        output.push_str("}\n");
        output
    }

    fn to_class_diagram(&self, uast: &UAST, title: Option<&str>) -> String {
        let mut output = String::new();

        // Header PlantUML
        output.push_str("@startuml\n");
        if let Some(t) = title {
            output.push_str(&format!("title {}\n", t));
        }
        output.push_str("skinparam classAttributeIconSize 0\n");
        output.push_str("skinparam shadowing false\n\n");

        // Definir estilos por tipo de nó
        output.push_str("class Program << (P,#FFAAAA) >>\n");
        output.push_str("class Function << (F,#AAFFAA) >>\n");
        output.push_str("class Class << (C,#AAAAFF) >>\n");
        output.push_str("class Variable << (V,#FFFFAA) >>\n");
        output.push_str("class Expression << (E,#FFAAFF) >>\n\n");

        // Gerar classes para nós da UAST
        let mut visited = HashSet::new();
        self.emit_class_nodes(uast, uast.root, &mut output, 0, &mut visited);

        // Gerar relações
        self.emit_class_relations(uast, &mut output);

        output.push_str("@enduml\n");
        output
    }

    fn emit_class_nodes(
        &self,
        uast: &UAST,
        node_id: NodeId,
        output: &mut String,
        depth: usize,
        visited: &mut HashSet<NodeId>,
    ) {
        if depth > self.max_depth || visited.contains(&node_id) {
            return;
        }
        visited.insert(node_id);

        let node = match uast.nodes.get(&node_id) {
            Some(n) => n,
            None => return,
        };

        // Nome da classe (sanitizado para PlantUML)
        let class_name = format!("N{}", node_id.0);
        let label = self.node_label_plantuml(node);
        let stereotype = self.node_stereotype(&node.kind);

        output.push_str(&format!(
            "class {} {} {{\n",
            class_name,
            stereotype
        ));
        output.push_str(&format!("  {}\n", label));

        if self.show_types {
            if let Some(ref si) = node.semantic_info {
                if let Some(ref ty) = si.type_info {
                    output.push_str(&format!("  --\n  type: {}\n", self.type_label(ty)));
                }
            }
        }

        output.push_str("}\n\n");

        // Emitir filhos
        for &child_id in &node.children {
            self.emit_class_nodes(uast, child_id, output, depth + 1, visited);
        }
    }

    fn emit_class_relations(&self, uast: &UAST, output: &mut String) {
        for node in uast.nodes.values() {
            for child in &node.children {
                output.push_str(&format!(
                    "{} *-- {}\n",
                    format!("N{}", node.id.0),
                    format!("N{}", child.0)
                ));
            }
        }
    }

    fn node_label_plantuml(&self, node: &UASTNode) -> String {
        let kind = format!("{:?}", node.kind);
        let mut label = kind;

        if let Some(name) = node.attributes.get("name") {
            if let AttributeValue::String(s) = name {
                label.push_str(&format!("\\n{}", s));
            }
        }

        // Escapar caracteres especiais do PlantUML
        label.replace('"', "\\\"").replace('{', "\\{").replace('}', "\\}")
    }

    fn node_stereotype(&self, kind: &NodeKind) -> &'static str {
        match kind {
            NodeKind::Program => "<< (P,#FFAAAA) >>",
            NodeKind::DeclFunction => "<< (F,#AAFFAA) >>",
            NodeKind::DeclVariable => "<< (V,#FFFFAA) >>",
            NodeKind::ExprLiteral | NodeKind::ExprIdentifier => "<< (E,#FFAAFF) >>",
            _ => "",
        }
    }

    fn type_label(&self, ty: &crate::ast::uast::TypeRef) -> String {
        if ty.generics.is_empty() {
            ty.name.clone()
        } else {
            let params: Vec<_> = ty.generics.iter().map(|g| self.type_label(g)).collect();
            format!("{}<{}>", ty.name, params.join(","))
        }
    }

    // ===== Activity Diagram =====

    fn to_activity_diagram(&self, uast: &UAST, title: Option<&str>) -> String {
        let mut output = String::new();

        output.push_str("@startuml\n");
        if let Some(t) = title {
            output.push_str(&format!("title {}\n", t));
        }
        output.push_str("start\n");

        // Percorrer fluxo de controle
        let mut visited = HashSet::new();
        self.emit_activity_flow(uast, uast.root, &mut output, &mut visited);

        output.push_str("stop\n@enduml\n");
        output
    }

    fn emit_activity_flow(
        &self,
        uast: &UAST,
        node_id: NodeId,
        output: &mut String,
        visited: &mut HashSet<NodeId>,
    ) {
        if visited.contains(&node_id) {
            return;
        }
        visited.insert(node_id);

        let node = match uast.nodes.get(&node_id) {
            Some(n) => n,
            None => return,
        };

        match &node.kind {
            NodeKind::StmtIf => {
                output.push_str(&format!("if ({}) then\n", self.node_label_plantuml(node)));
                for child_id in &node.children {
                    self.emit_activity_flow(uast, *child_id, output, visited);
                }
                output.push_str("endif\n");
            }
            NodeKind::ExprCall => {
                output.push_str(&format!(":Call {};\n", self.node_label_plantuml(node)));
            }
            NodeKind::ExprReturn => {
                output.push_str(&format!(":Return {};\n", self.node_label_plantuml(node)));
            }
            _ => {
                // Nó genérico
                let label = self.node_label_plantuml(node);
                if !label.is_empty() {
                    output.push_str(&format!(":{};\n", label));
                }
            }
        }
    }

    // ===== Sequence Diagram =====

    fn to_sequence_diagram(&self, uast: &UAST, title: Option<&str>) -> String {
        let mut output = String::new();

        output.push_str("@startuml\n");
        if let Some(t) = title {
            output.push_str(&format!("title {}\n", t));
        }
        output.push_str("autonumber\n\n");

        // Identificar participantes (funções/módulos)
        let participants = self.extract_participants(uast);
        for (id, name) in &participants {
            output.push_str(&format!("participant \"{}\" as {}\n", name, id));
        }
        output.push('\n');

        // Gerar mensagens de chamada
        self.emit_sequence_messages(uast, &participants, &mut output);

        output.push_str("@enduml\n");
        output
    }

    fn extract_participants(&self, uast: &UAST) -> HashMap<String, String> {
        let mut participants = HashMap::new();
        for (id, node) in &uast.nodes {
            if matches!(node.kind, NodeKind::DeclFunction) {
                if let Some(name) = node.attributes.get("name")
                    .and_then(|v| match v { AttributeValue::String(s) => Some(s.clone()), _ => None })
                {
                    participants.insert(format!("F{}", id.0), name.clone());
                }
            }
        }
        participants
    }

    fn emit_sequence_messages(
        &self,
        uast: &UAST,
        participants: &HashMap<String, String>,
        output: &mut String,
    ) {
        for node in uast.nodes.values() {
            if let NodeKind::ExprCall = node.kind {
                // Extrair função chamada e argumentos
                if let Some(callee_id) = node.children.first() {
                    if let Some(callee) = uast.nodes.get(callee_id) {
                        let callee_name = callee.attributes.get("name")
                            .and_then(|v| match v { AttributeValue::String(s) => Some(s.clone()), _ => None })
                            .unwrap_or_else(|| "unknown".to_string());

                        output.push_str(&format!("{} -> {}: {}\n",
                            "Main",  // Caller simplificado
                            participants.iter()
                                .find(|(_, name)| name == &&callee_name)
                                .map(|(id, _)| id.as_str())
                                .unwrap_or("Unknown"),
                            callee_name));
                    }
                }
            }
        }
    }
}
