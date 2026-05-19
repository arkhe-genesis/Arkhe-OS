# Creating Your First Arkhe Agent on Android

**Canon**: ∞.Ω.∇+++.244.android_integration
**Last Updated**: 2026-05-19
**Temporal Seal**: `r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0`

---

## 🎯 Objective

Create a constitutional Android Activity that:
- Calculates its own Φ_C coherence score
- Enforces P1-P7 guardrails automatically
- Anchors lifecycle events to TemporalChain
- Communicates via Token Arkhe Bus

---

## 📦 Prerequisites

```kotlin
// build.gradle.kts (app module)
dependencies {
    implementation("org.arkhe:arkhe-android-core:244.1.0")

    // Required for coroutines (ArkheCore uses suspend functions)
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.0")
}
```

```xml
<!-- AndroidManifest.xml -->
<application
    ...
    arkhe:substrate="243"
    arkhe:canon="∞.Ω.∇+++.244.android_integration"
    arkhe:phiCThreshold="0.85">

    <!-- Your Activity -->
    <activity
        android:name=".ConstitutionalAgentActivity"
        android:exported="true"
        arkhe:agentName="mobile_sentinel"
        arkhe:agentCapabilities="parse,verify,anchor"
        arkhe:minPhiC="0.80">
        <intent-filter>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent-filter>
    </activity>

</application>
```

---

## 🧱 Step 1: Create the Activity with Constitutional Guardrails

```kotlin
// ConstitutionalAgentActivity.kt
package com.example.arkhe

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.arkhe.android.core.ArkheCore
import org.arkhe.android.core.ConstitutionalPrinciple
import org.arkhe.android.guardrails.ArkheGuardrails

class ConstitutionalAgentActivity : AppCompatActivity() {

    private val arkheCore by lazy { ArkheCore.getInstance(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 🔐 Constitutional Guardrail: Verify P1-P7 before proceeding
        val verification = ArkheGuardrails.verifyActivityOnCreate(
            activity = this,
            principles = ConstitutionalPrinciple.values().toList()
        )

        if (!verification.passed) {
            // Handle constitutional violation
            handleConstitutionalViolation(verification)
            return
        }

        // ✅ Passed constitutional check — proceed with normal setup
        setContentView(R.layout.activity_constitutional_agent)

        // 📊 Calculate and display Φ_C for this Activity
        CoroutineScope(Dispatchers.Main).launch {
            val phiC = arkheCore.calculatePhiC(this@ConstitutionalAgentActivity::class.java)
            updatePhiCDisplay(phiC)
        }

        // 🔗 Anchor Activity creation to TemporalChain
        CoroutineScope(Dispatchers.IO).launch {
            arkheCore.anchorToTemporalChain(
                eventType = "activity_created",
                payload = mapOf(
                    "component" to this@ConstitutionalAgentActivity::class.java.simpleName,
                    "intent_action" to intent?.action,
                    "timestamp" to System.currentTimeMillis()
                )
            )
        }
    }

    private fun handleConstitutionalViolation(result: ConstitutionalVerificationResult) {
        // P1-P7 violation handling strategy
        when (result.violatedPrinciple) {
            ConstitutionalPrinciple.P1_VERIFICATION -> {
                // Missing formal specification — fallback to safe mode
                showSafeModeDialog("Formal specification required for this operation")
            }
            ConstitutionalPrinciple.P3_SOVEREIGN_GAP -> {
                // Φ_C >= 1.0 — inject novelty to preserve gap
                arkheCore.injectNoveltyFlux()
                recreate() // Restart with adjusted Φ_C
            }
            ConstitutionalPrinciple.P7_ENERGY_RESOURCE -> {
                // Energy budget exceeded — defer or throttle
                deferHighEnergyOperation()
            }
            else -> {
                // Generic fallback
                finish() // Safely exit if violation cannot be resolved
            }
        }
    }

    private fun updatePhiCDisplay(phiC: Float) {
        // Update UI with Φ_C score (0.0-1.0)
        findViewById<TextView>(R.id.phiCValue).text = String.format("%.3f", phiC)

        // Color-code based on coherence
        val color = when {
            phiC >= 0.95 -> R.color.phiC_excellent
            phiC >= 0.90 -> R.color.phiC_good
            phiC >= 0.85 -> R.color.phiC_acceptable
            else -> R.color.phiC_low
        }
        findViewById<TextView>(R.id.phiCValue).setTextColor(getColor(color))
    }
}
```

---

## 🧪 Step 2: Test Constitutional Compliance

```kotlin
// ConstitutionalAgentActivityTest.kt
package com.example.arkhe

import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.test.runTest
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.assertTrue

@RunWith(AndroidJUnit4::class)
class ConstitutionalAgentActivityTest {

    @Test
    fun `Activity passes constitutional verification on create`() = runTest {
        // Arrange
        val scenario = ActivityScenario.launch(ConstitutionalAgentActivity::class.java)

        // Act & Assert
        scenario.onActivity { activity ->
            // Verify Φ_C is calculated and < 1.0 (Sovereign Gap)
            val phiC = ArkheCore.getInstance(activity)
                .calculatePhiC(ConstitutionalAgentActivity::class.java)

            assertTrue("Φ_C must be < 1.0 (P3)", phiC < 1.0f)
            assertTrue("Φ_C should be >= 0.85 for operational components", phiC >= 0.85f)
        }
    }

    @Test
    fun `TemporalChain anchoring succeeds for lifecycle events`() = runTest {
        val scenario = ActivityScenario.launch(ConstitutionalAgentActivity::class.java)

        scenario.onActivity { activity ->
            // Anchoring is async; verify it was initiated
            // In real test: mock TemporalChain client and verify call
        }
    }
}
```

---

## 🔍 Step 3: Verify Canonical Compliance

Use the Arkhe CLI to validate your implementation:

```bash
# Install Arkhe CLI (requires Node.js 18+)
npm install -g @arkhe/cli

# Validate your Activity against constitutional principles
arkhe validate android \
  --source src/main/kotlin/com/example/arkhe/ConstitutionalAgentActivity.kt \
  --principles P1,P3,P6,P7 \
  --output validation-report.json

# View results
cat validation-report.json | jq '.results[] | select(.passed == false)'
```

Expected output for compliant code:
```json
{
  "canonical_compliance": true,
  "principles_verified": ["P1", "P3", "P6", "P7"],
  "phi_c_score": 0.942,
  "temporal_anchor": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
}
```

---

## 🚀 Next Steps

- [ ] Add Token Arkhe Bus messaging to your agent
- [ ] Implement PQC encryption for sensitive data
- [ ] Configure energy-aware permissions with P7 review
- [ ] Deploy to Firebase Test Lab for multi-device validation

---

## 🔗 Resources

- [ArkheCore API Reference](/android/api/ArkheCore)
- [Constitutional Principles Deep Dive](/android/core-concepts/constitutional-guardrails)
- [Example Project: Constitutional Agent](https://github.com/arkhe-org/arkhe-android-examples/tree/main/constitutional-activity)
- [TemporalChain Explorer](https://temporal.arkhe.org) — Verify anchors

**Canonical Seal for this Tutorial**: `s9t0u1v2w3x4y5z6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1`
