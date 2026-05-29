import os
import base64
import json
import hashlib

def b64(text):
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

# 274
sub274_dir = "substrates/t/274_arkhe_so"
os.makedirs(sub274_dir, exist_ok=True)

with open(f"{sub274_dir}/substrate.toml", "w") as f:
    f.write("""[substrate]
id = "274"
name = "ARKHE.SO"
status = "CANONIZED_PROVISIONAL"
""")

sub274_py = """import os
import tempfile
import json
import base64
import hashlib

class Substrato274ArkheSo:
    def __init__(self):
        self.substrate_id = "274"
        self.status = "CANONIZED_PROVISIONAL"
        self.canonical_seal = "e7f8a9b0c1d20000000000000000000000000000000000000000000000000274"
        self.b64_arkhe_ko = "{arkhe_ko}"
        self.b64_libarkhe_so = "{libarkhe_so}"
        self.b64_schema = "{schema}"

    def canonize(self):
        arkhe_ko = base64.b64decode(self.b64_arkhe_ko).decode("utf-8")
        libarkhe_so = base64.b64decode(self.b64_libarkhe_so).decode("utf-8")
        schema = base64.b64decode(self.b64_schema).decode("utf-8")

        report = {{
            "Substrate": self.substrate_id,
            "Status": self.status,
            "Canonical_Seal": self.canonical_seal,
            "Files": {{
                "arkhe.ko.rs": arkhe_ko,
                "libarkhe.h": libarkhe_so,
                "schema_274.yaml": schema
            }}
        }}

        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(report, f)

        print("Report generated at: " + path)
        return path

if __name__ == "__main__":
    canon = Substrato274ArkheSo()
    canon.canonize()
"""

arkhe_ko_274 = """// arkhe.ko — Linux Kernel Module (LKM)
// Substrato 274: Intercepta syscalls e ancora eventos na TemporalChain.
// Compilar com: make (Kbuild) + rustc --target x86_64-unknown-linux-musl

#![no_std]
#![feature(allocator_api)]

use kernel::prelude::*;
use kernel::netlink::{NetlinkSocket, NetlinkMessage};
use kernel::random::getrandom;
use kernel::crypto::{sha3_256, ed25519_sign};
use kernel::task::Task;

module! {
    type: ArkheModule,
    name: "arkhe",
    author: "ARKHE-OS Architect (ORCID 0009-0005-2697-4668)",
    description: "Kernel module for TemporalChain anchoring",
    license: "GPL v2",
}

struct ArkheModule {
    _netlink: NetlinkSocket,
    node_key: [u8; 64], // Ed25519 private key
}

impl KernelModule for ArkheModule {
    fn init(module: &'static ThisModule) -> Result<Self> {
        let netlink = NetlinkSocket::new(module, 31 /* ARKHE_FAMILY */)?;
        let node_key = load_key_from_tpm()?;

        // Registra hooks de syscall
        register_syscall_hook(SyscallOp::Open, sys_open_hook)?;
        register_syscall_hook(SyscallOp::Write, sys_write_hook)?;
        register_syscall_hook(SyscallOp::Execve, sys_execve_hook)?;

        Ok(ArkheModule { _netlink: netlink, node_key })
    }
}

// Hook para sys_open: captura abertura de arquivos
fn sys_open_hook(filename: &[u8], flags: u32, mode: u16) -> i64 {
    let event = construct_event("OPEN", filename, flags, mode);
    queue_event(&event);
    0 // prossegue execução normal
}

// Hook para sys_write: captura escrita em arquivos
fn sys_write_hook(fd: u32, buf: &[u8], count: usize) -> i64 {
    let event = construct_event_with_payload("WRITE", fd, buf, count);
    queue_event(&event);
    0
}

// Hook para sys_execve: captura execução de programas
fn sys_execve_hook(filename: &[u8], argv: &[&[u8]]) -> i64 {
    let event = construct_event("EXEC", filename, 0, 0);
    queue_event(&event);
    0
}

fn construct_event(op: &str, filename: &[u8], _flags: u32, _mode: u16) -> KernelEvent {
    let mut hasher = Sha3_256::new();
    hasher.update(op.as_bytes());
    hasher.update(filename);
    hasher.update(&current_task().pid.to_le_bytes());
    hasher.update(&get_time_ns().to_le_bytes());
    let hash = hasher.finalize();

    KernelEvent {
        op: op.to_string(),
        path: String::from_utf8_lossy(filename).to_string(),
        pid: current_task().pid,
        timestamp_ns: get_time_ns(),
        hash,
        signature: vec![], // será assinado na fila
    }
}
"""

libarkhe_so_274 = """// libarkhe.h — API pública para processos userspace
#ifndef ARKHE_H
#define ARKHE_H

#include <stdint.h>
#include <stddef.h>

// Inicializa a conexão com o módulo de kernel
int arkhe_init(void);

// Sela um arquivo (calcula hash e o ancora na TemporalChain)
int arkhe_seal(const char *path, char *seal_hash, size_t hash_len);

// Persiste um estado epistêmico (L0-L5)
int arkhe_commit(const char *intent, const void *state, size_t state_len);

// Recupera histórico de eventos para um arquivo
int arkhe_audit(const char *path, char *events_json, size_t json_len);

#endif // ARKHE_H
"""

schema_274 = """substrato:
  id: 274
  nome: ARKHE.SO (Linux Kernel Architecture)
  deidade: Nyx
  status: CANONIZED_PROVISIONAL
  descricao: >
    Arquitetura completa do sistema operacional Linux integrada à Catedral.
    Inclui módulo de kernel (arkhe.ko), daemon userspace (arkhed),
    biblioteca de sistema (libarkhe.so) e CLI (arkhe).
    Intercepta syscalls, ancora eventos na TemporalChain (923) e
    governa o sistema sob a Constituição P1-P7.
  componentes:
    - nome: arkhe.ko
      tipo: kernel_module
      linguagem: Rust
      funcao: Interceptar syscalls e gerar eventos assinados
    - nome: arkhed
      tipo: daemon
      linguagem: Go
      funcao: Receber eventos do kernel e ancorar na TemporalChain
    - nome: libarkhe.so
      tipo: shared_library
      linguagem: C
      funcao: API pública para processos userspace
    - nome: arkhe
      tipo: cli
      linguagem: Rust
      funcao: Ferramenta de administração e auditoria
  syscalls_interceptadas:
    - sys_open
    - sys_read
    - sys_write
    - sys_execve
    - sys_connect
    - sys_sendto
    - sys_mmap
    - sys_clone
  temporalchain:
    batch_size: 1000
    batch_interval_ms: 100
    l2_endpoint: "grpc://temporalchain.arkhe.cathedral:9230"
  cross_links:
    - 923 (TemporalChain)
    - 255 (Hermes ZK — assinatura Ed25519)
    - 262 (ARKHE-TCP — comunicação com mesh)
    - 912 (Epistemic Commit — persistência de estado)
    - 944 (Glasswing Sentinel — auditoria de arquivos)
"""

with open(f"{sub274_dir}/substrato_274_arkhe_so.py", "w") as f:
    f.write(sub274_py.format(
        arkhe_ko=b64(arkhe_ko_274),
        libarkhe_so=b64(libarkhe_so_274),
        schema=b64(schema_274)
    ))

# 275
sub275_dir = "substrates/t/275_arkhe_os"
os.makedirs(sub275_dir, exist_ok=True)

with open(f"{sub275_dir}/substrate.toml", "w") as f:
    f.write("""[substrate]
id = "275"
name = "ARKHE OS"
status = "CANONIZED_PROVISIONAL"
""")

sub275_py = """import os
import tempfile
import json
import base64
import hashlib

class Substrato275ArkheOs:
    def __init__(self):
        self.substrate_id = "275"
        self.status = "CANONIZED_PROVISIONAL"
        self.canonical_seal = "a1b2c3d4e5f60000000000000000000000000000000000000000000000000275"
        self.b64_schema = "{schema}"

    def canonize(self):
        schema = base64.b64decode(self.b64_schema).decode("utf-8")

        report = {{
            "Substrate": self.substrate_id,
            "Status": self.status,
            "Canonical_Seal": self.canonical_seal,
            "Files": {{
                "schema_275.yaml": schema
            }}
        }}

        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(report, f)

        print("Report generated at: " + path)
        return path

if __name__ == "__main__":
    canon = Substrato275ArkheOs()
    canon.canonize()
"""

schema_275 = """substrato:
  id: 275
  nome: ARKHE OS — Arquitetura Completa
  deidades: [Hécate, Nyx]
  status: CANONIZED_PROVISIONAL
  componentes:
    - { nome: arkhe.sys, tipo: driver_windows, linguagem: Rust, funcao: "Interceptar IRPs de I/O" }
    - { nome: arkhe.ko, tipo: lkm_linux, linguagem: Rust, funcao: "Interceptar syscalls via kprobe/LSM" }
    - { nome: arkhed, tipo: daemon, linguagem: Go, funcao: "Batch, assinar e ancorar na L2" }
    - { nome: libarkhe.so, tipo: shared_lib, linguagem: C, funcao: "API para processos userspace" }
    - { nome: arkhe, tipo: cli, linguagem: Rust, funcao: "Administração e auditoria" }
  eventos_interceptados:
    windows: [IRP_MJ_CREATE, IRP_MJ_WRITE, IRP_MJ_SET_INFORMATION]
    linux: [sys_open, sys_read, sys_write, sys_execve, sys_connect, sys_sendto, sys_mmap, sys_clone]
  ancoragem:
    batch_size: 1000
    batch_interval_ms: 100
    l2_endpoint: "grpc://temporalchain.arkhe.cathedral:9230"
  cross_links:
    - 923 (TemporalChain)
    - 255 (Hermes ZK)
    - 912 (Epistemic Commit)
    - 944 (Glasswing Sentinel)
"""

with open(f"{sub275_dir}/substrato_275_arkhe_os.py", "w") as f:
    f.write(sub275_py.format(
        schema=b64(schema_275)
    ))
