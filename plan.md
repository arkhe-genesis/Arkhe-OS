1. **Create Substrate Directory and `substrate.toml`:**
   - Create directory `substrates/t/766_trapdoor_countermeasure/`
   - Create `substrate.toml` with `id=766`, `name="TRAPDOOR-COUNTERMEASURE"`, `status="CANONIZED_CLEAN"`, `namespace="t"`, etc., similar to `765`.

2. **Create Python Canonization Script (`substrato_766_trapdoor_countermeasure.py`):**
   - Create a class `Substrato766TrapdoorCountermeasure` that defines the decree content based on the problem description.
   - Define base64 strings containing the payloads for the 5 layers specified in the decree:
     - `arkhe-security-gate.js` (Layer 1)
     - `arkhe-static-analyzer.js` (Layer 2)
     - `arkhe-runtime-monitor.js` (Layer 3)
     - `arkhe-ci-gate.yml` (Layer 4)
     - `arkhe-incident-response.js` (Layer 5)
   - Ensure the python script does NOT use f-strings to strictly follow Arkhe OS invariants.
   - Calculate SHA3-256 seal.
   - Export output to a canonical JSON file using `tempfile.mkstemp(suffix=".json", text=True)`.

3. **Integrate with `arkhe.js` (Substrate 765):**
   - Modify `core/arkhe-js/arkhe.js` to add the `enableTrapdoorCountermeasures` function to the `Arkhe` class or create a `Security` module as per the "INTEGRAÇÃO COM ARKHE.JS" section.
   - Add `status()` function inside the security module to return the metrics requested.
   - Do the equivalent modifications inside `core/arkhe-js/arkhe.d.ts` so it matches the JS implementation.
   - Ensure tests in `arkhe.test.js` still pass, and optionally add tests for the new security module.

4. **Integrate tests in `test_substrates.py`:**
   - Add test `test_substrato_766_trapdoor_countermeasure()` that loads and runs the canonizer script, verifies the generated JSON, and asserts zero f-strings.

5. **Pre-commit Steps:**
   - Perform testing, verifications, reviews and reflections.

6. **Submit:**
   - Submit changes as branch `feat/766-trapdoor-countermeasure`.
