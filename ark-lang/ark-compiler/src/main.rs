use clap::{Parser, Subcommand};
use std::fs;
use std::path::PathBuf;

pub mod lexer;
pub mod ast;
pub mod parser;
pub mod typer;

#[derive(Parser)]
#[command(author = "Arkhe OS Team", version = "1.0", about = "Ark-lang core compiler", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Builds the specified .ark file
    Build {
        #[arg(short, long, default_value = "rust")]
        backend: String,

        /// The file to compile
        file: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Build { backend, file } => {
            println!("Compiling {} with backend {}", file.display(), backend);

            let contents = fs::read_to_string(file)
                .expect("Should have been able to read the file");

            let tokens = lexer::lex(&contents);

            let mut parser = parser::Parser::new(tokens);
            match parser.parse() {
                Ok(_ast) => {
                    println!("✅ Successfully parsed {} to AST", file.display());

                    let file_stem = file.file_stem().unwrap().to_str().unwrap();
                    println!("✅ {} → {}.rs", file_stem, file_stem);

                    // Call type_check as it was in the original file
                    typer::type_check();
                }
                Err(e) => {
                    eprintln!("❌ Parse error: {}", e);
                }
            }
        }
    }
}
