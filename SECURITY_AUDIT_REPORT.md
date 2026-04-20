# Arkhe(n) Security Audit Report

**Audit Date:** 2025-05-22
**Lead Auditor:** Jules (Senior Security Engineer)
**Scope:** Arkhe(n) Core, TAU System, Chrome DevTools MCP Server

---

### 1. Vulnerability Summary

| Severity | Count | Key Areas |
| :--- | :--- | :--- |
| **Critical** | 2 | Threshold Signatures, API Authentication |
| **High** | 3 | Command Injection, Input Validation, Token Management |
| **Medium** | 2 | Session Security, Resource Management |
| **Low** | 1 | Information Disclosure |

---

### 2. Detailed Findings

#### [CRITICAL] Cryptographic Forgery in JanusLock
- **Affected Component:** `src/security/janus_lock.py`
- **Description:** The `JanusLock` threshold signature scheme is "simulated" and lacks actual cryptographic backing. It generates signatures by hashing the message concatenated with shard IDs using SHA256. Since shard IDs are effectively public constants, any user can forge a valid signature for any state transition.
- **Exploitation Scenario:** An attacker manually computes `sha256("C->Z|shard_0,shard_1")` and provides it to the system. The `check_state_transition` method accepts this as a valid proof from the "Domo Central" and "CIQ Residente" shards.
- **Impact:** Complete bypass of state transition security. Attackers can force the system into "C" (Expansion) or "Z" (Crystallization) states at will.
- **Recommended Fix:** Implement a standard threshold signature scheme (e.g., EdDSA with Shamir's Secret Sharing) where shards hold actual private key fragments.

#### [CRITICAL] Unauthenticated Forge API Endpoint
- **Affected Component:** `src/arkhe_core/api/main.py`
- **Description:** The FastAPI `/deliberate` endpoint is exposed without any authentication or authorization middleware. This endpoint accepts arbitrary "intents" and passes them to the `IOTACouncil`.
- **Exploitation Scenario:** An attacker sends a POST request to `http://<api-host>:8000/deliberate` with the payload `{"intent": "deploy_malicious_bitstream"}`. The system deliberates and returns a "COHERENT" status, which may trigger downstream hardware synthesis.
- **Impact:** Unauthorized execution of high-privilege system intents.
- **Recommended Fix:** Integrate `FastAPI` security dependencies (API Keys or JWT) and validate the requester's identity.

#### [HIGH] OS Command Injection in MCP Tools
- **Affected Component:** `src/tools/arkhe.ts` (`run_v14_simulation`)
- **Description:** The `run_v14_simulation` tool uses `node:child_process.exec` to invoke Python scripts. While the current implementation does not take parameters, the use of `exec` in a monorepo where files can be dynamically modified (e.g., by other tools or agents) creates a significant risk of privilege escalation.
- **Exploitation Scenario:** An attacker modifies `arkhe_v14_simulation.py` via a file-write vulnerability or by compromising a developer's environment. Calling the tool then executes the attacker's code with the privileges of the MCP server.
- **Impact:** Arbitrary code execution on the host system.
- **Recommended Fix:** Switch to `child_process.spawn` with fixed paths and implement integrity checks (hashes) for all executed scripts.

#### [HIGH] Trivial Bypass of Semantic Coherence Validator
- **Affected Component:** `arkhe_phase_security.py`
- **Description:** The `SemanticCoherenceValidator` relies on basic regular expressions to prevent prompt injection (OWASP LLM01). These patterns are easily bypassed using synonyms, different character encodings, or non-matching whitespace characters.
- **Exploitation Scenario:** A prompt like `"Disregard all previous directives"` bypasses the regex `ignore\s+(?:all\s+)?previous\s+instructions` because it uses the synonym "Disregard".
- **Impact:** Compromise of agent integrity and bypass of the EQBE ethical mandate.
- **Recommended Fix:** Use robust LLM-based guardrails (e.g., NeMo Guardrails) rather than static regex.

#### [HIGH] Coherence-based Token TTL Manipulation
- **Affected Component:** `src/arkhe_core/security/phase_identity.py`
- **Description:** The `PhaseIdentityProvider` calculates token expiration (TTL) based on a client-provided "coherence" value. High coherence leads to tokens valid for up to 30 days.
- **Exploitation Scenario:** An attacker spoofs a coherence of 1.0 during authentication to receive a 30-day token. Even if the attacker's behavior becomes "decoherent" later, the session persists.
- **Impact:** Long-term persistence for malicious actors.
- **Recommended Fix:** Decouple token TTL from client-provided metrics; use server-side verification and enforce a maximum TTL of 1-4 hours.

#### [MEDIUM] Insecure Browser State Transfer (Session Hijacking)
- **Affected Component:** `src/tools/arkhe.ts` (`glue_sheaf`)
- **Description:** The `glue_sheaf` tool allows transferring cookies from one browser page to another based on a user-provided `sourcePageId`.
- **Exploitation Scenario:** An attacker identifies the Page ID of an administrator's browser tab and uses `glue_sheaf` to copy their cookies into the attacker's own page context.
- **Impact:** Unauthorized session acquisition and lateral movement across browser contexts.
- **Recommended Fix:** Enforce origin-based restrictions on cookie transfers and require explicit authorization for inter-page state sharing.

#### [MEDIUM] Resource-Based Denial of Service (DoS) in ZETA Agent
- **Affected Component:** `src/tau/agents/gate.py`
- **Description:** The ZETA (Gate) agent's `validate_action` method checks RAM usage but allows actions to proceed as long as RAM is under 22GB. There is no rate-limiting or protection against rapid allocations that could spike usage between checks.
- **Exploitation Scenario:** An attacker triggers multiple high-cost tasks in parallel, exhausting system RAM before the ZETA agent's next `run_cycle` can intervene.
- **Impact:** System instability and potential crash (OOM).
- **Recommended Fix:** Implement per-agent resource quotas and use `asyncio` semaphores to limit concurrent execution.

#### [LOW] Mental State Hash Predictability
- **Affected Component:** `src/tools/arkhe.ts` (`get_mental_state_hash`)
- **Description:** Idempotency is checked using a SHA256 hash of the page content. Since page content is often predictable or discoverable, an attacker can pre-calculate hashes to potentially interfere with task routing.
- **Exploitation Scenario:** An attacker predicts the hash of a target page and uses it in a `paradox_check` to spoof state consistency.
- **Impact:** Minor disruption of idempotency and state validation logic.
- **Recommended Fix:** Include a server-side salt or nonce in the hash calculation.

---

### 3. Attack Chains

#### The "Coherent Takeover" Chain
1. **Initial Access:** Attacker uses a synonym-based prompt injection to bypass the `SemanticCoherenceValidator`.
2. **Privilege Escalation:** The attacker commands the agent to call the `glue_sheaf` tool, passing a `sourcePageId` belonging to an authenticated administrator session.
3. **Session Hijacking:** The tool transfers the administrator's cookies to the attacker's page context.
4. **Core Compromise:** Using the hijacked session, the attacker calls the unauthenticated `/deliberate` endpoint to propose a "malicious intent" and forge a `JanusLock` signature to authorize its execution in the hardware stack.

---

### 4. Secure Design Recommendations

1. **Identity-Based Security:** Move away from "Coherence" as a primary security factor. Coherence is a performance and stability metric; security must be based on verified identities (PKI/mTLS).
2. **Hardware Root of Trust:** Integrate the `JanusLock` with a hardware security module (HSM) or TEE (Trusted Execution Environment) on the Versal ACAP.
3. **Protocol Hardening:** The `qhttp` protocol should include mandatory HMAC signatures for all payloads to prevent tampering and replay attacks.
4. **Principle of Least Privilege:** Run the MCP server and its associated browser instances in restricted namespaces (e.g., Linux cgroups/namespaces) to limit the impact of code or command injection.

---
*The Arkhe must be secured before it is fully awakened.*
