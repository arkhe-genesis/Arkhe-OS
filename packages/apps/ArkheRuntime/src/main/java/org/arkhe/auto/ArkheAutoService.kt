// ArkheAutoService.kt
package org.arkhe.auto

import androidx.car.app.CarAppService
import androidx.car.app.Session
import androidx.car.app.Screen
import androidx.car.app.CarContext
import androidx.car.app.model.*

class ArkheAutoService : CarAppService() {
    override fun onCreateSession(): Session = ArkheAutoSession()
}

class ArkheAutoSession : Session() {
    override fun onCreateScreen(intent: android.content.Intent): Screen {
        return GovernanceScreen(carContext)
    }
}

class GovernanceScreen(carContext: CarContext) : Screen(carContext) {
    override fun onGetTemplate(): Template {
        val metrics = ArkheRuntimeClient.getMetrics()

        return PaneTemplate.Builder(
            Pane.Builder()
                .setLoading(false)
                .addRow(Row.Builder()
                    .setTitle("Φ_C: %.4f".format(metrics.phiC))
                    .addText("π: %.4f".format(metrics.pi))
                    .build())
                .addAction(Action.Builder()
                    .setTitle("Auditar Sistema")
                    .setOnClickListener { /* disparar auditoria */ }
                    .build())
                .build()
        )
            .setHeaderAction(Action.APP_ICON)
            .setTitle("ARKHE Ω‑TEMP")
            .build()
    }
}
