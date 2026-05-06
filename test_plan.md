1. **Understand the Objective**: The goal is to add C# and C++ frontend parsers and backend generators to the "Polymath Parser". This involves using the `github.com/smacker/go-tree-sitter` library and its respective language grammars to extract Abstract Syntax Trees (ASTs) for C# and C++, converting them to a unified Lingua Franca Intermediate Representation (LFIR), and generating idiomatic code for the two target languages.

2. **Files to Update**:
    - Based on the exploration, the parser system exists in two main locations: `arkhe_os/parser/polymath.go` and `arkhe_os/transcompiler/polymath_parser.go`.
    - Looking at the tests running, both seem to be valid, but I'll apply the C# and C++ frontends and backends logic to both of them. Actually, wait. Let me double check if `arkhe_os/parser/polymath.go` has a `go.mod`. Yes, it does. `arkhe_os/transcompiler` also has a `go.mod`. I should update both to ensure consistency across the codebase. I just updated both.
    - Let's double check `arkhe_os/parser/polymath.go` and `arkhe_os/transcompiler/polymath_parser.go` are the only places that need the `registerAdditionalLanguages` call.

3. **Pre-commit Steps**:
   - I will call `pre_commit_instructions` to find out what verification steps are needed before submission.

4. **Submission**:
   - Create a commit and submit via `submit` tool.
