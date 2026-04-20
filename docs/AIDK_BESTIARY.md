# AIDK Bestiary Specification (Draft v1.0)
## Mapping Vulnerabilities to Ludic Entities

This document defines the recommended mapping between corporate security vulnerabilities (CWE/CVE) and game entities (monsters, obstacles, environmental effects) to maintain the **Quartz Wall**'s semantic separation.

### 1. Mapping Philosophy
Game designers should not name monsters "SQL Injection". Instead, they should use the **Visual Metaphor** that corresponds to the vulnerability's behavior.

### 2. The Core Bestiary

| Vulnerability Type | Ludic Name | Visual Metaphor | Suggested Action |
| :--- | :--- | :--- | :--- |
| **SQL Injection (CWE-89)** | Stone Worm | A creature that burrows into the foundation (database). | Interaction/Audit |
| **Information Exposure (CWE-200)** | Shadow Leak | A dark fluid or smoke leaking from a container. | Scan/Containment |
| **Broken Auth (CWE-287)** | Doppelgänger | A mimic or shapeshifter attempting to bypass gates. | Identity Verification |
| **Command Injection (CWE-78)** | Void Swarm | A chaotic swarm that overrides environment controls. | Cleansing Spell |
| **Config Drift** | Rust/Corruption | Visual decay or color shifting of static structures. | Calibration/Repair |

### 3. Severity Color Palette

| Severity | Color (Hex) | Visual Effect |
| :--- | :--- | :--- |
| **Low** | #00FFAA | Static Glow |
| **Medium** | #FFAA33 | Slow Pulse |
| **High** | #FF5A1A | Fast Ripple |
| **Critical** | #FF3333 | Explosive/Chaos |

### 4. Implementation in the Quartz Wall
The Muralha de Quartzo (API Gateway) will use these mappings to translate ludic telemetria into security events without the player ever seeing the technical terms.
