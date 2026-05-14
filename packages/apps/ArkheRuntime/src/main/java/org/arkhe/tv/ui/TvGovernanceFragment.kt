// TvGovernanceFragment.kt
package org.arkhe.tv.ui

import android.os.Bundle
import androidx.leanback.app.GuidedStepSupportFragment
import androidx.leanback.widget.GuidanceStylist
import androidx.leanback.widget.GuidedAction
import org.arkhe.runtime.R

class TvGovernanceFragment : GuidedStepSupportFragment() {
    override fun onCreateGuidance(savedInstanceState: Bundle?): GuidanceStylist.Guidance {
        val metrics = ArkheRuntimeClient.getMetrics()
        return GuidanceStylist.Guidance(
            "ARKHE Ω‑TEMP ASI Governance",
            "Φ_C Global: %.4f\nπ Global: %.4f\nNós Conectados: %d\nArquivos Selados: %d".format(
                metrics.phiC, metrics.pi, metrics.peerCount, metrics.sealedFiles
            ),
            "Dashboard de Governança",
            resources.getDrawable(R.drawable.ic_arkhe_banner, null)
        )
    }

    override fun onCreateActions(actions: MutableList<GuidedAction>, savedInstanceState: Bundle?) {
        actions.add(GuidedAction.Builder(context)
            .title("🛡️ Executar Spiral Ping")
            .description("Força auditoria de governança global")
            .build())
        actions.add(GuidedAction.Builder(context)
            .title("📊 Ver Histórico de Decisões")
            .build())
    }
}
