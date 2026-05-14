// GovernanceWidgetProvider.kt
package org.arkhe.runtime.widget

import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.widget.RemoteViews
import org.arkhe.runtime.R

class GovernanceWidgetProvider : AppWidgetProvider() {
    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (widgetId in appWidgetIds) {
            val views = RemoteViews(context.packageName, R.layout.widget_governance)

            // Buscar métricas do serviço (via IPC)
            val metrics = ArkheRuntimeClient.getMetrics()

            views.setTextViewText(R.id.tv_phi_c, "Φ_C: %.4f".format(metrics.phiC))
            views.setTextViewText(R.id.tv_pi, "π: %.4f".format(metrics.pi))
            views.setTextViewText(R.id.tv_peers, "Pares: %d".format(metrics.peerCount))
            views.setProgressBar(R.id.pb_phi_c, 1000, (metrics.phiC * 1000).toInt(), false)

            // Botão de ping manual
            val pingIntent = ArkheRuntimeClient.getPingIntent(context)
            views.setOnClickPendingIntent(R.id.btn_ping, pingIntent)

            appWidgetManager.updateAppWidget(widgetId, views)
        }
    }
}
