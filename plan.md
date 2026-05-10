1. **Add `recordMitoticEvent` to `AuditLedger`:**
   - It will log the split of a parent node into two daughter nodes ("MITOSIS").
2. **Add `validateG2Checkpoint` to `TemporalConsistencyOracle`:**
   - Verify the ledger/chain genome.
3. **Expose `oracle_` from `RetrocausalValidator`:**
   - Add a getter for the `oracle_` instance so the mitotic router can call the G2 checkpoint validation.
4. **Add `deepCopy` to `TemporalHashChain`:**
   - Allow cloning the chain.
5. **Modify `RetroRouter` access modifiers:**
   - Change `private` variables to `protected` so `MitoticRouter` can inherit from it and use the variables (`chain_`, `node_id_`, `validator_`, etc).
   - Add a `node_id()` getter.
6. **Implement `MitoticRouter` class in `arkhe_cpp.cpp`:**
   - Implement `synthesisPhase` to copy the chain.
   - Implement `anaphaseDispatch` to send messages to sisters.
   - Implement `cytokinesis` to instantiate the new daughter routers and record the mitosis.
7. **Complete pre-commit steps:**
   - Ensure proper testing, verification, review, and reflection are done.
1. **Understand the problem**: The goal is to implement the ARKHE Ω-TEMP protocol using x86-64 assembly language (NASM syntax) based on the provided project structure and source files. The structure comprises multiple modules (`arkhe.asm`, `temporal.asm`, `keccak.asm`, `oracle.asm`, `heap.asm`, `dijkstra.asm`, `merkle.asm`, `bn128.asm`, `falcon.asm`, `routing.asm`, `shield.asm`, `syscall.asm`, `trie.asm`) and a main `Makefile`.
2. **Current state**: I have already created the initial directory structure, copied the provided code into their respective `.asm` files, created the `arkhe.inc` header file with required constants and macros, and created the `Makefile`. I have also fixed various syntax and compilation errors across multiple files (like undefined symbols, unaligned jumps/calls, fixing FPU instruction mismatches with SIMD in `heap.asm`, fixing the Makefile for proper object linking). Currently, the codebase successfully compiles and runs the `run_tests` binary.
3. **Completing Pre-Commit Steps**:
   - I need to run `pre_commit_instructions` to fetch validation/review instructions.
   - I will review the final codebase to ensure there are no lingering compilation warnings or errors that signify broken logic, although the `run_tests` binary works.
   - The user requested that we shouldn't use high-level abstraction and strictly rely on the hardware.
   - Ensure the structure strictly matches `arkhe-asm/src`, `arkhe-asm/include`, `arkhe-asm/test` etc.
4. **Finalizing**:
   - Execute the code, prove that `make verify` and `make` both pass without critical errors and produce the expected binaries.
   - Submit the changes under the requested format.
