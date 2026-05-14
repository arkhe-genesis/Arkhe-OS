1.  **Implement the Lexer in `ark-lang/ark-compiler/src/lexer.rs`**
    *   Use the `logos` crate to define the tokens for Ark-lang based on the specification.
    *   Tokens will include keywords (`block`, `prove`, `anchor`, `pay`, `pretend`, `quantum`, `entropy`, `coherence`, `q_art`, `vortex`, `orcid`, `pix`, `multiversal`, `let`, `fn`, `if`, `else`, `for`, `in`, `return`, `import`, `as`, `from`, `type`, `struct`, `enum`, `trait`, `impl`, `true`, `false`, `zk`, `Secret`, `Temporal`, `Qubit`, `Influence`, `Entropy`, `Coherence`, `block_id`, `linear`, `mut`, `pub`, `self`, `Self`, `where`).
    *   Tokens will include primitives (`Int`, `Float`, `Bool`, `String`, `Byte`, `Unit`).
    *   Tokens will include identifiers, integers, floats, strings, and byte literals based on the provided regex.
    *   Handle single-line and multi-line comments.

2.  **Define the AST (Abstract Syntax Tree)**
    *   Create `ark-lang/ark-compiler/src/ast.rs` to hold the AST definitions.
    *   Define types for primitive values, expressions (including function calls, macro calls like `prove`, `anchor`, `$(...)`), statements (`let`, assignments, control flow), definitions (`fn`, `struct`, `enum`, `trait`, `impl`), and the `block` construct.

3.  **Implement the Parser in `ark-lang/ark-compiler/src/parser.rs`**
    *   Implement a recursive descent parser (or use a parser combinator library if preferred, but manual might be easier for a simple spec) that takes the token stream and produces an AST.
    *   Handle parsing of top-level items, blocks, statements, and expressions.
    *   Make sure to capture the `#[linear]` attribute for types.

4.  **Implement the `main.rs` CLI**
    *   Use `clap` to create a basic CLI with a `build` subcommand.
    *   The `build` subcommand should take a file, read its contents, lex it, and parse it. (We can stub the actual code generation to Rust/WASM/Solidity for now if the task is just to get the lexing/parsing/AST up and running, but I will prepare a basic rust codegen stub to match the output in the spec).

5.  **Pre-commit steps**
    *   Ensure proper testing, verification, review, and reflection are done before submitting the final changes.

6.  **Submit**
    *   Commit and push the implementation of Ark-lang v1.0 core.
1. **Understand the Goal**: Integrate `kimi_cathedral_node.py` as a proper Arkhe OS Substrato (Substrato 305/154). The file currently exists in the root directory.
2. **Examine `kimi_cathedral_node.py`**: It implements `KimiCathedralAPI`, `QHTTPClient`, `WheelerMeshNode`, `OrchestratorV149`, and `KimiCathedralNode`. The user's goal seems to be to integrate this Node implementation into the Arkhe OS Cathedral Architecture.
3. **Check the memory instructions**:
    - "Arkhe OS canonizes foundational distributed system components as Substratos 0 through 9 ... implemented in Python as standalone files at the repository root following the naming convention `substrato_X_name.py`."
    - What about Substratos 154 / 305? The title is: "Kimi-Cathedral Node — Integrated Implementation v7.3.1 + qhttp:// (Substrate 305) + Orchestrator v149 (Substrate 154)".
    - I should probably add `kimi_cathedral_node.py` as `substrato_305_kimi_cathedral.py` or similar, or just leave it as `kimi_cathedral_node.py` (since I created it in the repo root from the user's prompt). Oh wait! The user provided the code for `kimi_cathedral_node.py` in the chat!
    - "I should probably rename the file or integrate it into `arkhe_os`?" Let's see the user's request. Wait, there is no explicit instruction other than providing the code block.
    - If the user provides a code block for "Kimi-Cathedral Node — Integrated Implementation v7.3.1 + qhttp:// (Substrate 305) + Orchestrator v149 (Substrate 154)", the standard operation is to integrate it and ensure the tests pass and the code is saved.
    - Let's read the task again: The user provided a Python script. I have already saved it to `kimi_cathedral_node.py` and written tests in `test_kimi_cathedral.py`. The tests passed! Wait, what else is needed?
    - Is there any `pre_commit_instructions`? Let's check.
