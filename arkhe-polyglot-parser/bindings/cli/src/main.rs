use clap::{Parser, Subcommand};
use std::path::PathBuf;
use parser_core::PolyglotParser;

#[derive(Parser)]
#[command(
    name = "arkhe-polyglot",
    about = "ARKHE Polymath-Polyglot Parser (Substrato 6061)",
    long_about = "O intérprete universal da Catedral. Compreende todas as linguagens como dialetos de uma mesma verdade formal."
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// Nível de otimização (0-3)
    #[arg(short, long, default_value_t = 2)]
    optimize: u8,

    /// Modo estrito (erros fatais)
    #[arg(short, long)]
    strict: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// Detectar linguagem de um arquivo
    Detect {
        /// Arquivo para analisar
        file: PathBuf,
    },

    /// Parse um arquivo e gerar UAST
    Parse {
        /// Arquivo para parsear
        file: PathBuf,

        /// Linguagem (auto-detectada se omitido)
        #[arg(short, long)]
        language: Option<String>,

        /// Formato de saída: json, text, dot
        #[arg(short, long, default_value = "json")]
        format: String,
    },

    /// Gerar documentação (PlantUML, Graphviz)
    Docs {
        /// Arquivo para analisar
        file: PathBuf,

        /// Formato de saída: mermaid, dot, plantuml, graphviz
        #[arg(short, long, default_value = "plantuml")]
        format: String,

        /// Tipo de diagrama PlantUML: class, activity, sequence
        #[arg(long, default_value = "class")]
        plantuml_type: String,
    },
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Detect { file } => {
            let parser = PolyglotParser::new(None);
            println!("Detecting language for file: {:?}", file);
            let content = std::fs::read_to_string(&file)?;
            let detection = parser.detect_language(&content, file.file_name().and_then(|n| n.to_str()));
            println!("Language detected: {:?}", detection.language);
        },
        Commands::Parse { file, language, format: _ } => {
            println!("Parsing file: {:?} with language {:?}", file, language);
        },
        Commands::Docs { file, format, plantuml_type } => {
            let mut parser = PolyglotParser::new(None);
            let content = std::fs::read_to_string(&file)?;
            let parse_result = parser.parse(&content, file.file_name().and_then(|n| n.to_str())).map_err(|e| e.to_string())?;

            let docs = match format.as_str() {
                "plantuml" => {
                    let puml_type = match plantuml_type.as_str() {
                        "activity" => parser_core::docs::plantuml_generator::PlantUMLType::ActivityDiagram,
                        "sequence" => parser_core::docs::plantuml_generator::PlantUMLType::SequenceDiagram,
                        _ => parser_core::docs::plantuml_generator::PlantUMLType::ClassDiagram,
                    };
                    let gen = parser_core::docs::plantuml_generator::PlantUMLDocGenerator::new(puml_type);
                    gen.to_plantuml(&parse_result.uast, file.file_name().and_then(|n| n.to_str()))
                }
                "graphviz" | "dot" => {
                    let gen = parser_core::docs::plantuml_generator::PlantUMLDocGenerator::new(parser_core::docs::plantuml_generator::PlantUMLType::Graphviz);
                    gen.to_plantuml(&parse_result.uast, file.file_name().and_then(|n| n.to_str()))
                }
                _ => return Err(format!("Formato não suportado: {}", format).into()),
            };

            println!("{}", docs);
        },
    }

    Ok(())
}
