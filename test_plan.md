1. **SpacetimeGraph**
   - Create `src/visual` inside `arkhe-cosmological` containing `mod.rs`, `node.rs`, `edge.rs`, `physics.rs`, and `render.rs`.
   - Update `arkhe-cosmological/Cargo.toml` to include dependencies `serde`, `serde_json`, and `nalgebra`.
   - Create structs `VisualNode`, `NodeType`, and `MotorType` in `node.rs`.
   - Add `render_graph` in `render.rs`.
   - Ensure the new module is exported in `src/lib.rs`.
   - Ensure tests pass via `cargo test`.
2. **Shard Orchestration (`cmd/arkhe`)**
   - Create a new crate in `cmd/arkhe` with a `Cargo.toml` specifying `clap`, `tonic`, `prost`, `serde`, `serde_json`, and `tokio`.
   - Add a `src/main.rs` that uses `clap` for the main CLI.
   - Implement the `shard` and `self-complete` mock commands in `src/commands/shard.rs` and `src/commands/self_complete.rs`.
   - Ensure it passes `cargo check`.
3. **Portal Financial**
   - Implement the mock `QArtEngine::process_new_art_block_auto` logic in `arkhe-qart/substrate-6072/src/engine.rs` (by making a mock `auto_royalty` module).
   - We must also mock `VisualNode::update_financial_dashboard` in the `node.rs` from Step 1.
4. **Auto-completion**
   - Implemented within `cmd/arkhe` from step 2 via the `self-complete` command logic mocking the auto-trigger loops.
5. **Pre Commit**
   - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
