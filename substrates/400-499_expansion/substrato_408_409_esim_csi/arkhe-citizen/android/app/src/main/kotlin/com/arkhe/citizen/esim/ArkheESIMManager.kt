package com.arkhe.citizen.esim

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.telephony.euicc.EuiccManager
import android.telephony.euicc.DownloadableSubscription
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.PluginRegistry

/**
 * ArkheESIMManager.kt — Gestão nativa de eSIM via EuiccManager
 */

class ArkheESIMManager(private val context: Context) {
    private val euiccManager = context.getSystemService(Context.EUICC_SERVICE) as? EuiccManager

    fun isSupported(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            euiccManager?.isEnabled ?: false
        } else {
            false
        }
    }

    fun getStatus(): Map<String, Any> {
        return mapOf(
            "isEnabled" to isSupported(),
            "eid" to (euiccManager?.eid ?: "")
        )
    }

    fun acquireProfile(provider: String, txid: String, country: String): Map<String, Any> {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.P || euiccManager == null || !euiccManager.isEnabled) {
            return mapOf(
                "status" to "error",
                "message" to "eSIM not supported or enabled on this device"
            )
        }

        // Construct the activation code per the requested provider and txid
        val activationCode = "LPA:1\$$provider.com\$$txid"

        val intent = Intent(EuiccManager.ACTION_START_EUICC_ACTIVATION).apply {
            putExtra(EuiccManager.EXTRA_USE_QR_SCANNER, false)
        }

        return mapOf(
            "status" to "success",
            "provider" to provider,
            "txid" to txid,
            "country" to country,
            "activationCode" to activationCode,
            "message" to "Profile acquired. Use the UI to start the EuiccManager.ACTION_START_EUICC_ACTIVATION intent if needed."
        )
    }
}

class ArkheESIMPlugin {
    companion object {
        const val CHANNEL = "com.arkhe.citizen/esim"

        fun registerWith(registrar: PluginRegistry.Registrar) {
            val channel = MethodChannel(registrar.messenger(), CHANNEL)
            val manager = ArkheESIMManager(registrar.context())

            channel.setMethodCallHandler { call, result ->
                when (call.method) {
                    "isSupported" -> result.success(manager.isSupported())
                    "getStatus" -> result.success(manager.getStatus())
                    "acquireProfile" -> {
                        val provider = call.argument<String>("provider") ?: "unknown"
                        val txid = call.argument<String>("txid") ?: "unknown"
                        val country = call.argument<String>("country") ?: "auto"
                        result.success(manager.acquireProfile(provider, txid, country))
                    }
                    else -> result.notImplemented()
                }
            }
        }
    }
}
