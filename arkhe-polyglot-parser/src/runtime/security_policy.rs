// ============================================================================
// ARKHE P³ — Security Policy Engine
// ============================================================================
// Motor de políticas de segurança para execução sandbox.
// Define o que o código transpilado pode e não pode fazer.
//
// Inspirado em:
//   - WebAssembly sandboxing
//   - seccomp-bpf (Linux)
//   - Cap'n Proto capability model
//   - Deno permission model
// ============================================================================

use std::collections::HashSet;
use crate::runtime::polyglot_vm::SandboxLevel;

/// Política de segurança aplicável a uma execução
pub struct SecurityPolicy {
    pub level: SandboxLevel,
    pub max_execution_time_ms: u64,
    pub max_memory_bytes: usize,
    pub max_instructions: u64,
    pub allowed_hosts: HashSet<String>,
    pub allowed_paths: HashSet<String>,
    pub blocked_syscalls: HashSet<String>,
    pub require_signature: bool,       // Requer assinatura ARKHE
    pub max_message_size: usize,       // Para comunicação inter-shard
    pub enable_temporal_checks: bool,  // Verificar coerência temporal
    pub arkhe_oracle_url: Option<String>, // URL do Oracle para validação
}

impl Default for SecurityPolicy {
    fn default() -> Self {
        Self {
            level: SandboxLevel::Standard,
            max_execution_time_ms: 5000,
            max_memory_bytes: 64 * 1024 * 1024, // 64MB
            max_instructions: 1_000_000_000,
            allowed_hosts: HashSet::new(),
            allowed_paths: HashSet::new(),
            blocked_syscalls: Self::default_blocked_syscalls(),
            require_signature: false,
            max_message_size: 1024 * 1024, // 1MB
            enable_temporal_checks: true,
            arkhe_oracle_url: None,
        }
    }
}

impl SecurityPolicy {
    /// Syscalls bloqueadas por padrão
    fn default_blocked_syscalls() -> HashSet<String> {
        [
            "execve", "fork", "vfork", "clone", "ptrace",
            "mount", "umount", "kexec", "reboot",
            "mknod", "init_module", "delete_module",
            "socket", "bind", "listen", "accept", "connect",
            "sendmsg", "recvmsg",
            "openat"
        ].iter().map(|s| s.to_string()).collect()
    }

    /// Policy para análise estática (sem execução)
    pub fn static_analysis() -> Self {
        Self {
            level: SandboxLevel::Hermit,
            require_signature: true,
            enable_temporal_checks: true,
            ..Default::default()
        }
    }

    /// Policy para execução em ambiente confiável
    pub fn trusted_execution() -> Self {
        Self {
            level: SandboxLevel::Full,
            max_execution_time_ms: 60000,
            max_memory_bytes: 4 * 1024 * 1024 * 1024, // 4GB
            require_signature: false,
            ..Default::default()
        }
    }

    /// Policy para execução pública (não-confiável)
    pub fn untrusted_execution() -> Self {
        Self {
            level: SandboxLevel::Pure,
            max_execution_time_ms: 1000,
            max_memory_bytes: 16 * 1024 * 1024, // 16MB
            max_instructions: 10_000_000,
            require_signature: true,
            enable_temporal_checks: true,
            ..Default::default()
        }
    }
}
