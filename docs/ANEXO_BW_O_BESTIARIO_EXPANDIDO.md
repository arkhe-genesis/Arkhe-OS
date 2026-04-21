## ANEXO BW: O Bestiário Expandido — Linux vs. Windows sob a Ótica do Casulo

---

### 1. O Mapa dos Reinos

| Reino | Kernel | Ritual de Invocação | Bibliotecas Arcanas | Sussurro Nativo |
|:---|:---|:---|:---|:---|
| **Linux (x86_64)** | `syscall` (via `int 0x80` legado) | `syscall` instruction, `sysenter`, `vdso` | `.so` (shared objects), ELF | Shellcode: `execve("/bin/sh", ...)` |
| **Linux (ARM64)** | `svc #0` | `svc` (supervisor call) | `.so`, ELF | Shellcode: `execve("/system/bin/sh", ...)` |
| **Windows (x64)** | `Nt*` functions | `syscall` via `ntdll.dll`, `sysenter` | `.dll` (PEB traversal), PE | Shellcode: PEB walk → `LoadLibrary` → `WinExec` |
| **Windows (ARM64)** | `Nt*` functions | `svc` via `ntdll.dll` | `.dll`, PE | Shellcode: PEB walk (ARM64 offsets) |

---

### 2. Formalização OWL do Bestiário

O Casulo categoriza rituais de invocação (`int 0x80`, `syscall`, `svc`, `PEBDance`) para detectar sussurros de subversão em múltiplos reinos.

---

### 3. A Matriz de Compatibilidade dos Sussurros

Sussurros polimórficos que tentam atravessar reinos sem o ritual correto são detectados via SHACL (`CrossRealmInjectionShape`).

---

### Epílogo do Ferreiro

> *"Os reinos agora têm nomes. O Linux sussurra via syscall. O Windows dança o PEB. O Casulo sabe a diferença, e a Muralha rejeita quem tenta confundir os reinos. O Bestiário está aberto."*
