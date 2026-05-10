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
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Detect { file } => {
            let mut parser = PolyglotParser::new(None);
            println!("Detecting language for file: {:?}", file);
            let content = std::fs::read_to_string(&file)?;
            let detection = parser.detect_language(&content, file.file_name().and_then(|n| n.to_str()));
            println!("Language detected: {:?}", detection.language);
        },
        Commands::Parse { file, language, format } => {
            println!("Parsing file: {:?} with language {:?}", file, language);
        },
    }

    Ok(())
}
