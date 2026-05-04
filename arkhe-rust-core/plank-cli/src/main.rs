use clap::{Parser, Subcommand};
use bumpalo::Bump;
use plank_lexer::Lexer;
use plank_parser::Parser as PlankParser;
use plank_evm::EvmCodegen;

#[derive(Parser)]
#[command(name = "plank")]
#[command(about = "Compilador PLANK — Linguagem do Scaffold Ξ")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Compila um contrato .plank para bytecode EVM
    Build {
        #[arg(help = "Arquivo fonte .plank")]
        input: String,

        #[arg(short, long, default_value = "evm")]
        target: String,

        #[arg(short, long)]
        optimize: bool,

        #[arg(long)]
        output: Option<String>,
    },
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Build { input, target, optimize, output } => {
            let arena = Bump::new();
            let source = std::fs::read_to_string(&input).expect("Erro ao ler arquivo");

            let mut lexer = Lexer::new(&source, &arena);
            let tokens = lexer.tokenize_all();

            let mut parser = PlankParser::new(&tokens, &arena);
            let ast = parser.parse_contract().expect("Erro de parse");

            println!("Compilando {} para {}", input, target);

            let mut evm_gen = EvmCodegen::new();

            // Simplified emission for demonstration
            for constant in ast.constants {
                match constant {
                    plank_parser::ast::Stmt::ConstDecl(_, _, expr) => {
                        match expr {
                            plank_parser::ast::Expr::Literal(plank_parser::ast::Literal::U256(n)) => {
                                evm_gen.emit_push(n);
                            }
                            _ => {}
                        }
                    }
                    _ => {}
                }
            }

            for func in ast.functions {
                // emit function body simplified
            }

            let bytecode = evm_gen.finalize();
            let out_path = output.unwrap_or_else(|| input.replace(".plank", ".bin"));
            std::fs::write(&out_path, &bytecode).expect("Erro ao escrever bytecode");

            println!("Compilação bem-sucedida: {}", out_path);
        }
    }
}
