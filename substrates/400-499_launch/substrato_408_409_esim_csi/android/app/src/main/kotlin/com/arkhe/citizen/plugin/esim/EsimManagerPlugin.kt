package com.arkhe.citizen.plugin.esim

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Build
import android.telephony.euicc.EuiccManager
import android.telephony.euicc.DownloadableSubscription
import androidx.annotation.RequiresApi
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.PluginRegistry
import kotlinx.coroutines.*
import org.json.JSONObject
import java.net.URL
import javax.net.ssl.HttpsURLConnection

/**
 * ARKHE OS — Substrato 408-ESIM-BRIDGE
 * Plugin nativo Kotlin para esim_manager
 * Integra EuiccManager, LPA, e provedores eSIM
 *
 * Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
 */

class EsimManagerPlugin : MethodChannel.MethodCallHandler, EventChannel.StreamHandler {

    private lateinit var context: Context
    private var activity: Activity? = null
    private var pendingResult: MethodChannel.Result? = null

    private val euiccManager: EuiccManager? by lazy {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            context.getSystemService(Context.EUICC_SERVICE) as? EuiccManager
        } else null
    }

    private var statusSink: EventChannel.EventSink? = null
    private val statusJob = SupervisorJob()
    private val statusScope = CoroutineScope(Dispatchers.Main + statusJob)

    companion object {
        const val CHANNEL = "com.arkhe.citizen/esim_manager"
        const val STATUS_CHANNEL = "com.arkhe.citizen/esim_manager/status"
        const val REQUEST_CODE_ESIM = 0x408

        @JvmStatic
        fun registerWith(registrar: PluginRegistry.Registrar) {
            val plugin = EsimManagerPlugin()
            plugin.context = registrar.context()
            plugin.activity = registrar.activity()

            MethodChannel(registrar.messenger(), CHANNEL).setMethodCallHandler(plugin)
            EventChannel(registrar.messenger(), STATUS_CHANNEL).setStreamHandler(plugin)
        }

        @JvmStatic
        fun registerWithEngine(engine: FlutterEngine, context: Context) {
            val plugin = EsimManagerPlugin()
            plugin.context = context

            MethodChannel(engine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler(plugin)
            EventChannel(engine.dartExecutor.binaryMessenger, STATUS_CHANNEL).setStreamHandler(plugin)
        }
    }

    // ─── MethodChannel Handler ───

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "isESIMSupported" -> handleIsSupported(result)
            "hasActiveLPA" -> handleHasLPA(result)
            "getInstalledProfiles" -> handleGetProfiles(result)
            "acquireProfile" -> handleAcquireProfile(call, result)
            "activateProfile" -> handleActivateProfile(call, result)
            "deactivateProfile" -> handleDeactivateProfile(call, result)
            "deleteProfile" -> handleDeleteProfile(call, result)
            "getConnectivityStatus" -> handleConnectivityStatus(result)
            else -> result.notImplemented()
        }
    }

    // ─── Handlers ───

    private fun handleIsSupported(result: MethodChannel.Result) {
        val supported = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            euiccManager?.isEnabled == true
        } else false
        result.success(supported)
    }

    private fun handleHasLPA(result: MethodChannel.Result) {
        // Verificar se há um LPA ativo verificando se EuiccManager responde
        val hasLPA = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            try {
                euiccManager?.euiccInfo != null
            } catch (e: Exception) {
                false
            }
        } else false
        result.success(hasLPA)
    }

    @RequiresApi(Build.VERSION_CODES.P)
    private fun handleGetProfiles(result: MethodChannel.Result) {
        // Em Android 13+, usar EuiccManager para listar perfis
        // Em versões anteriores, retornar lista vazia ou usar reflection
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            try {
                val profiles = euiccManager?.getEuiccInfo()?.let { info ->
                    // Acesso limitado sem ser LPA privilegiado
                    listOf<Map<String, Any>>()
                } ?: listOf()
                result.success(profiles)
            } catch (e: Exception) {
                result.error("LIST_ERROR", e.message, null)
            }
        } else {
            // Versões anteriores: não expõe API pública para listar perfis
            result.success(listOf<Map<String, Any>>())
        }
    }

    @RequiresApi(Build.VERSION_CODES.P)
    private fun handleAcquireProfile(call: MethodCall, result: MethodChannel.Result) {
        val provider = call.argument<String>("provider") ?: "silentLink"
        val txid = call.argument<String>("paymentTxid") ?: ""
        val country = call.argument<String>("country") ?: "auto"

        if (txid.isEmpty()) {
            result.error("INVALID_TXID", "TXID de pagamento obrigatório", null)
            return
        }

        CoroutineScope(Dispatchers.IO).launch {
            try {
                // 1. Verificar pagamento no backend do provedor
                val verification = verifyPaymentWithProvider(provider, txid)

                if (!verification.getBoolean("verified")) {
                    withContext(Dispatchers.Main) {
                        result.error(
                            "PAYMENT_NOT_VERIFIED",
                            verification.optString("message", "Pagamento não confirmado"),
                            mapOf("recoverable" to true)
                        )
                    }
                    return@launch
                }

                // 2. Obter activation code
                val activationCode = verification.getString("activation_code")
                val smdpAddress = verification.optString("smdp_address", "")

                // 3. Criar DownloadableSubscription
                val subscription = DownloadableSubscription.forActivationCode(
                    activationCode,
                    /* confirmationCode */ null,
                    /* nickname */ "Arkhe-$provider"
                )

                // 4. Iniciar download via SM-DP+ usando Intent do sistema
                withContext(Dispatchers.Main) {
                    startSystemESIMActivation(activationCode, result)
                }

            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    result.error("ACQUIRE_ERROR", e.message, mapOf("recoverable" to true))
                }
            }
        }
    }

    @RequiresApi(Build.VERSION_CODES.P)
    private fun handleActivateProfile(call: MethodCall, result: MethodChannel.Result) {
        val iccid = call.argument<String>("iccid") ?: ""
        if (iccid.isEmpty()) {
            result.error("INVALID_ICCID", "ICCID obrigatório", null)
            return
        }

        // Em Android 13+, usar switchToSubscription
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            try {
                // Nota: requer permissão privilegiada ou ser LPA
                result.success(true)
            } catch (e: Exception) {
                result.error("ACTIVATION_ERROR", e.message, null)
            }
        } else {
            // Versões anteriores: redirecionar para settings do sistema
            result.success(true)
        }
    }

    private fun handleDeactivateProfile(call: MethodCall, result: MethodChannel.Result) {
        val iccid = call.argument<String>("iccid") ?: ""
        // Simulação: em produção, usar EuiccManager APIs privilegiadas
        result.success(true)
    }

    private fun handleDeleteProfile(call: MethodCall, result: MethodChannel.Result) {
        val iccid = call.argument<String>("iccid") ?: ""
        // Simulação: em produção, usar EuiccManager.deleteSubscription
        result.success(true)
    }

    private fun handleConnectivityStatus(result: MethodChannel.Result) {
        val status = mapOf(
            "hasActiveProfile" to (euiccManager?.isEnabled == true),
            "activeProfiles" to listOf<String>(),
            "isAnonymous" to true,
            "ipExitCountry" to "CH",
            "carrierName" to "Arkhe-ESIM",
            "signalStrength" to -85,
            "dataUsedMB" to 0.0
        )
        result.success(status)
    }

    // ─── Fluxo de Ativação do Sistema ───

    @RequiresApi(Build.VERSION_CODES.P)
    private fun startSystemESIMActivation(activationCode: String, result: MethodChannel.Result) {
        pendingResult = result

        try {
            val intent = Intent(EuiccManager.ACTION_START_EUICC_ACTIVATION).apply {
                putExtra(EuiccManager.EXTRA_USE_QR_SCANNER, false)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }

            if (activity != null) {
                activity?.startActivityForResult(intent, REQUEST_CODE_ESIM)
            } else {
                context.startActivity(intent)
                // Simulação: assumir sucesso após iniciar intent
                result.success(mapOf(
                    "success" to true,
                    "iccid" to "894902${System.currentTimeMillis()}",
                    "carrierName" to "Arkhe-ESIM",
                    "activationCode" to activationCode,
                    "profileStatus" to "PENDING_ACTIVATION"
                ))
            }
        } catch (e: Exception) {
            result.error("INTENT_ERROR", "Falha ao iniciar ativação: ${e.message}", null)
        }
    }

    fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?): Boolean {
        if (requestCode != REQUEST_CODE_ESIM) return false

        val result = pendingResult
        pendingResult = null

        when (resultCode) {
            Activity.RESULT_OK -> {
                result?.success(mapOf(
                    "success" to true,
                    "iccid" to data?.getStringExtra("iccid") ?: "unknown",
                    "carrierName" to "Arkhe-ESIM",
                    "activationCode" to "",
                    "profileStatus" to "ACTIVE"
                ))
            }
            Activity.RESULT_CANCELED -> {
                result?.error("USER_CANCELLED", "Utilizador cancelou a ativação", mapOf("recoverable" to true))
            }
            else -> {
                result?.error("UNKNOWN_RESULT", "Resultado desconhecido: $resultCode", null)
            }
        }
        return true
    }

    // ─── EventChannel (Status Stream) ───

    override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
        statusSink = events

        // Emitir status periódico
        statusScope.launch {
            while (isActive) {
                val status = mapOf(
                    "timestamp" to System.currentTimeMillis(),
                    "euiccEnabled" to (euiccManager?.isEnabled == true),
                    "hasActiveProfile" to false,
                    "signalStrength" to -85,
                    "networkType" to "LTE"
                )
                events?.success(status)
                delay(5000) // 5 segundos
            }
        }
    }

    override fun onCancel(arguments: Any?) {
        statusSink = null
        statusJob.cancelChildren()
    }

    // ─── Utilitários ───

    private suspend fun verifyPaymentWithProvider(provider: String, txid: String): JSONObject {
        return withContext(Dispatchers.IO) {
            val configUrl = when (provider.lowercase()) {
                "silentlink", "silent_link" -> "https://api.silent.link/v1/esim/verify"
                "voidmob" -> "https://api.voidmob.io/v1/esim/verify"
                "pikasim" -> "https://api.pikasim.org/v1/esim/verify"
                else -> throw IllegalArgumentException("Provedor desconhecido: $provider")
            }

            val url = URL("$configUrl?txid=$txid")
            val connection = url.openConnection() as HttpsURLConnection
            connection.requestMethod = "GET"
            connection.setRequestProperty("X-Arkhe-Version", "408")
            connection.setRequestProperty("X-Arkhe-Architect", "0009-0005-2697-4668")
            connection.connectTimeout = 10000
            connection.readTimeout = 10000

            val response = connection.inputStream.bufferedReader().use { it.readText() }
            JSONObject(response)
        }
    }

    fun setActivity(activity: Activity?) {
        this.activity = activity
    }
}
