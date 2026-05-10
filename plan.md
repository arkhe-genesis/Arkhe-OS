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
