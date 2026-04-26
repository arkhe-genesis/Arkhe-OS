use crate::ast::*;

// -----------------------------------------------------------------------------
// ARKHE(N) COMPILER ALPHA
// Compiles ArkheLang (⍉) to Graphene-TPU Instructions and ZK-STARKs
// -----------------------------------------------------------------------------

pub struct Compiler {
    target: CompileTarget,
}

pub enum CompileTarget {
    GrapheneTPU,
    ArkheOS_Native, // x86_64 / RISC-V bare metal
    Cairo_STARK,    // Compiles to Cairo for ZK proofs
}

impl Compiler {
    pub fn new(target: CompileTarget) -> Self {
        Compiler { target }
    }

    pub fn compile(&self, program: &Program) -> String {
        let mut output = String::new();

        output.push_str(";; ARKHE(N) COMPILED BYTECODE\n");
        output.push_str(&format!(";; TARGET: {:?}\n\n", self.target_name()));

        for func in &program.functions {
            output.push_str(&self.compile_function(func));
        }

        output
    }

    fn target_name(&self) -> &str {
        match self.target {
            CompileTarget::GrapheneTPU => "GRAPHENE_TPU_V1",
            CompileTarget::ArkheOS_Native => "ARKHE_OS_BAREMETAL",
            CompileTarget::Cairo_STARK => "CAIRO_STARKNET",
        }
    }

    fn compile_function(&self, func: &Function) -> String {
        let mut asm = String::new();

        if func.is_retro {
            asm.push_str(&format!("@RETRO_ENTRY {}\n", func.name));
            asm.push_str("  OP_PHASE_LOCK  ;; Lock Kuramoto oscillator\n");
        } else {
            asm.push_str(&format!("{}:\n", func.name));
        }

        for stmt in &func.body {
            asm.push_str(&self.compile_stmt(stmt));
        }

        if func.is_retro {
            asm.push_str("  OP_COLLAPSE    ;; Interferometric collapse\n");
        }
        asm.push_str("  RET\n\n");

        asm
    }

    fn compile_stmt(&self, stmt: &Stmt) -> String {
        match stmt {
            Stmt::BranchVar(name, _, expr) => {
                let mut asm = format!("  OP_FDB_ALLOC {} ;; Allocate in FractalDB\n", name);
                asm.push_str(&self.compile_expr(expr));
                asm
            },
            Stmt::Commit(expr) => {
                let mut asm = self.compile_expr(expr);
                asm.push_str("  OP_FDB_COMMIT  ;; Prune divergent timelines\n");
                asm
            },
            Stmt::Let(name, _, expr) => {
                let mut asm = format!("  OP_ALLOC {}    ;; Standard phase-tagged alloc\n", name);
                asm.push_str(&self.compile_expr(expr));
                asm
            },
            Stmt::Assign(name, expr) => {
                let mut asm = self.compile_expr(expr);
                asm.push_str(&format!("  OP_STORE {}    ;; Assign value\n", name));
                asm
            },
            Stmt::Expr(expr) => {
                self.compile_expr(expr)
            },
        }
    }

    fn compile_expr(&self, expr: &Expr) -> String {
        match expr {
            Expr::Literal(val) => {
                format!("  OP_PUSH {}     ;; Push literal\n", val)
            },
            Expr::PhaseLiteral(real, imag) => {
                format!("  OP_PUSH_PHASE {}, {} ;; Push complex phase\n", real, imag)
            },
            Expr::Identifier(name) => {
                format!("  OP_LOAD {}     ;; Load variable\n", name)
            },
            Expr::RetrocausalBlock { condition, body, future_context } => {
                let mut asm = String::new();
                asm.push_str(&format!("  ;; Retrocausal Block (Context: {})\n", future_context));
                asm.push_str(&self.compile_expr(condition));
                asm.push_str("  OP_JMP_NOT_PHASE_LOCKED end_retro\n");
                for stmt in body {
                    asm.push_str(&self.compile_stmt(stmt));
                }
                asm.push_str("end_retro:\n");
                asm
            },
            Expr::InterferenceMax { branches, evaluator } => {
                let mut asm = String::new();
                asm.push_str("  ;; Interference Max\n");
                for branch in branches {
                    asm.push_str(&self.compile_expr(branch));
                }
                asm.push_str(&self.compile_expr(evaluator));
                asm.push_str("  OP_INTERFERE_MAX\n");
                asm
            },
            Expr::Prove(inner_expr) => {
                let mut asm = String::new();
                asm.push_str("  ;; ZK-STARK Proof Generation (Phase Transition)\n");
                asm.push_str("  ;; Reference: server/circuits/water_balance.circom & ebpf_integrity.circom\n");
                asm.push_str("  OP_ZK_PROVE_BEGIN\n");

                // Compile the inner expression which defines the logic to be proven
                asm.push_str(&self.compile_expr(inner_expr));

                asm.push_str("  OP_ZK_PROVE_END\n");
                asm.push_str("  OP_EMIT_NULLIFIER ;; Prevent replay attacks\n");
                asm
            },
            Expr::SheetGet => {
                "  OP_FD_SHEET_GET\n".to_string()
            },
            Expr::SheetSet(target) => {
                let mut asm = self.compile_expr(target);
                asm.push_str("  OP_FD_SHEET_SET\n");
                asm
            },
            Expr::SheetJump(target, state) => {
                let mut asm = self.compile_expr(target);
                asm.push_str(&self.compile_expr(state));
                asm.push_str("  OP_FD_SHEET_JUMP\n");
                asm
            },
            Expr::SheetProbe(target) => {
                let mut asm = self.compile_expr(target);
                asm.push_str("  OP_FD_SHEET_PROBE\n");
                asm
            },
            Expr::ArkheVerify(rho, sigma) => {
                let mut asm = self.compile_expr(rho);
                asm.push_str(&self.compile_expr(sigma));
                asm.push_str("  OP_ARKHE_VERIFY\n");
                asm
            },
            Expr::QnetFiber(photon, length) => {
                let mut asm = self.compile_expr(photon);
                asm.push_str(&self.compile_expr(length));
                asm.push_str("  OP_QNET_FIBER\n");
                asm
            },
        }
    }
}
