// ArkhePhiCComplication.kt
package org.arkhe.wear.complication

import androidx.wear.watchface.complications.data.ComplicationData
import androidx.wear.watchface.complications.data.ShortTextComplicationData
import androidx.wear.watchface.complications.datasource.ComplicationProviderService
import androidx.wear.watchface.complications.datasource.ComplicationRequest

class ArkhePhiCComplication : ComplicationProviderService() {
    override fun onComplicationRequest(request: ComplicationRequest): ComplicationData {
        val phiC = ArkheRuntimeClient.getPhiC()
        return ShortTextComplicationData.Builder(
            plainText = "Φ_C: %.4f".format(phiC),
            contentDescription = "Coerência ASI"
        ).build()
    }
}
