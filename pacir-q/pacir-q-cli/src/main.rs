//! pacir-q CLI.
use clap::{Parser, Subcommand};
use pacir_q_core::{
    alpha::{ALPHA_PACIR_OMEGA, ALPHA_REJECTED},
    falsifiers::*,
    quops::{verified_scores, QuopsState, TARGET_FEMOCO_Q, TARGET_RSA_2048_Q},
    spec_error::SpecificationDefect,
};

#[derive(Parser)]
#[command(name = "pacir-q", version, about = "PACIR-Ω para QUOPS")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    Alpha,
    Report,
    Falsify {
        #[arg(long)]
        id: String,
        #[arg(long)]
        q0: Option<f64>,
        #[arg(long)]
        q1: Option<f64>,
        #[arg(long)]
        years: Option<f64>,
        #[arg(long, default_value_t = 4.0)]
        expected: f64,
    },
}
fn main() {
    match Cli::parse().command {
        Command::Alpha => alpha(),
        Command::Report => report(),
        Command::Falsify {
            id,
            q0,
            q1,
            years,
            expected,
        } => falsify(&id, q0, q1, years, expected),
    }
}
fn alpha() {
    let defect = SpecificationDefect::article_threshold_defect();
    println!("α canónico PACIR-Ω = {:.13}\nα rejeitado (erro)  = {:.13}\nRácio (√e)          = {:.13}\n\nDefeito registado:\n  locus     = {}\n  declarado = {}\n  real      = {:.13}\n  impacto   = {}\n  resolvido = {}", ALPHA_PACIR_OMEGA, ALPHA_REJECTED, ALPHA_PACIR_OMEGA / ALPHA_REJECTED, defect.locus, defect.declared, defect.actual, defect.impact, defect.is_resolved(ALPHA_PACIR_OMEGA));
}
fn report() {
    println!(
        "{:<20} {:>10} {:>14} {:>10}\n{}",
        "Sistema",
        "QUOPS",
        "QUOPS/s",
        "Sucesso",
        "-".repeat(60)
    );
    for s in verified_scores() {
        println!(
            "{:<20} {:>10.1} {:>14.3e} {:>10}",
            s.system_name,
            s.q,
            s.omega,
            s.is_successful()
        );
    }
    let helios =
        QuopsState::new("Helios-1".into(), 98, 1504.0, 303.0, 0.65).expect("valid reference score");
    println!("\nLacuna Helios-1 → RSA-2048 = {:.2} ordens de magnitude\nLacuna Helios-1 → FeMoco   = {:.2} ordens de magnitude", helios.gap_orders(TARGET_RSA_2048_Q), helios.gap_orders(TARGET_FEMOCO_Q));
}
fn falsify(id: &str, q0: Option<f64>, q1: Option<f64>, years: Option<f64>, expected: f64) {
    let result = match id {
        "F1" => falsify_physical_quops_ceiling(q1.unwrap_or(0.0), 1.0e4),
        "F2" => falsify_ftqc_record(q1.unwrap_or(0.0), q0.unwrap_or(0.0)),
        "F3" => falsify_quops_growth(
            q0.unwrap_or(0.0),
            q1.unwrap_or(0.0),
            years.unwrap_or(4.0),
            expected,
        ),
        "F4" => falsify_rsa_target(q1.unwrap_or(0.0), 1.0e8),
        other => {
            eprintln!("Falsificador desconhecido: {other}");
            std::process::exit(2)
        }
    };
    println!(
        "Falsificador {id} = {}",
        if result { "FALSIFICADO" } else { "OK" }
    );
}
