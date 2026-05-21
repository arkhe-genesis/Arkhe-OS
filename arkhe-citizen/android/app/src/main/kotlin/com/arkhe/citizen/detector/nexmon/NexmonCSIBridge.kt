package com.arkhe.citizen.detector.nexmon

import android.content.Context
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.io.*
import java.net.*
import kotlin.math.*

/**
 * ARKHE OS — Substrato 409-NEXMON-CSI
 * Bridge nativa Kotlin para Nexmon em dispositivos Broadcom/Cypress
 *
 * Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
 * Requisitos: ROOT + Magisk + modulo nexmon_csi_arkhe instalado
 */

sealed class NexmonResult {
    data class Frame(
        val timestampNs: Long,
        val chipFamily: String,
        val channel: Int,
        val bandwidth: Int,
        val rssi: Int,
        val macAddress: String,
        val frameType: String,
        val rate: Int,
        val rawData: ByteArray
    ) : NexmonResult()

    data class Error(
        val code: Int,
        val message: String,
        val recoverable: Boolean
    ) : NexmonResult()

    object NotRooted : NexmonResult()
    object ModuleNotInstalled : NexmonResult()
    object DeviceNotSupported : NexmonResult()
}

class NexmonCSIBridge(private val context: Context) {

    private val _frameFlow = MutableSharedFlow<NexmonResult.Frame>(extraBufferCapacity = 200)
    val frameFlow: SharedFlow<NexmonResult.Frame> = _frameFlow.asSharedFlow()

    private var captureJob: Job? = null
    private var isRunning = false
    private var detectedChip: String = "unknown"

    // Configuracao de deteccao
    private val particleSignatures = mapOf(
        "muon" to floatArrayOf(0.8f, 0.6f, 0.4f, 0.3f, 0.2f),
        "electron" to floatArrayOf(0.5f, 0.7f, 0.5f, 0.3f, 0.1f),
        "photon" to floatArrayOf(0.3f, 0.4f, 0.5f, 0.4f, 0.3f),
    )

    /**
     * Verifica prerequisitos: root, modulo Magisk, chip suportado
     */
    fun checkPrerequisites(): Map<String, Any> {
        val hasRoot = checkRootAccess()
        val hasNexutil = File("/system/bin/nexutil").exists()
        val hasDevice = File("/dev/nexmon_csi").exists()
        val chipInfo = detectChipFamily()

        return mapOf(
            "hasRoot" to hasRoot,
            "hasNexutil" to hasNexutil,
            "hasDevice" to hasDevice,
            "chipFamily" to chipInfo,
            "ready" to (hasRoot && hasNexutil && hasDevice),
            "needsMagiskModule" to (hasRoot && !hasNexutil)
        )
    }

    /**
     * Inicia captura de frames 802.11 via Nexmon
     */
    fun startCapture(
        channel: Int = 6,
        bandwidth: Int = 20,
        filter: String = "0x88"
    ): NexmonResult {
        val prereqs = checkPrerequisites()

        if (!(prereqs["hasRoot"] as Boolean)) {
            return NexmonResult.NotRooted
        }

        if (!(prereqs["hasNexutil"] as Boolean)) {
            return NexmonResult.ModuleNotInstalled
        }

        if (!(prereqs["hasDevice"] as Boolean)) {
            // Tentar ativar via nexutil
            // Sanitize filter and channel
            val safeChannel = channel.coerceIn(1, 165)
            val safeFilter = filter.replace(Regex("[^a-zA-Z0-9xX]"), "")
            activateNexmon(safeChannel, safeFilter)

            // Verificar novamente
            if (!File("/dev/nexmon_csi").exists()) {
                return NexmonResult.Error(
                    code = 500,
                    message = "Falha ao ativar /dev/nexmon_csi",
                    recoverable = true
                )
            }
        }

        detectedChip = prereqs["chipFamily"] as String
        isRunning = true

        captureJob = CoroutineScope(Dispatchers.IO).launch {
            captureFromDevice(channel, bandwidth)
        }

        return NexmonResult.Frame(
            timestampNs = System.nanoTime(),
            chipFamily = detectedChip,
            channel = channel,
            bandwidth = bandwidth,
            rssi = -50,
            macAddress = "00:00:00:00:00:00",
            frameType = "init",
            rate = 0,
            rawData = ByteArray(0)
        )
    }

    fun stopCapture() {
        isRunning = false
        captureJob?.cancel()
        captureJob = null

        // Desativar modo monitor
        try {
            Runtime.getRuntime().exec("su -c 'nexutil -m0'")
        } catch (e: Exception) {
            Log.w("ArkheNexmon", "Falha ao desativar modo monitor: ${e.message}")
        }
    }

    /**
     * Processa frame 802.11 para deteccao de particulas
     * Analisa perturbacoes no trafego como proxy para deteccao
     */
    fun processFrameForParticles(frame: NexmonResult.Frame): ParticleDetection? {
        // Extrair metricas do frame
        val metrics = extractMetrics(frame.rawData)

        // Correlacionar com assinaturas
        var bestMatch = "unknown"
        var bestScore = 0.0f

        for ((particle, signature) in particleSignatures) {
            val score = correlateSignatures(metrics, signature)
            if (score > bestScore && score > 0.6f) {
                bestScore = score
                bestMatch = particle
            }
        }

        if (bestMatch == "unknown") return null

        return ParticleDetection(
            particleType = bestMatch,
            confidence = bestScore,
            energyKeV = estimateEnergyFromRSSI(frame.rssi, frame.rate),
            timestampNs = frame.timestampNs,
            sourceFrame = frame
        )
    }

    // ─── Captura de frames ───

    private suspend fun captureFromDevice(channel: Int, bandwidth: Int) {
        val deviceFile = File("/dev/nexmon_csi")

        while (isRunning) {
            try {
                if (!deviceFile.exists()) {
                    delay(1000)
                    continue
                }

                val fis = FileInputStream(deviceFile)
                val buffer = ByteArray(4096)

                while (isRunning) {
                    val bytesRead = fis.read(buffer)
                    if (bytesRead > 0) {
                        val frame = parseNexmonFrame(buffer.copyOf(bytesRead))
                        _frameFlow.emit(frame)
                    }
                }

                fis.close()
            } catch (e: Exception) {
                Log.e("ArkheNexmon", "Erro na captura: ${e.message}")
                delay(1000)
            }
        }
    }

    private fun parseNexmonFrame(data: ByteArray): NexmonResult.Frame {
        // Formato Nexmon: header + frame 802.11
        // Header: 12 bytes (magic + version + length + flags)
        // Frame 802.11: variavel

        val headerSize = 12
        val frameSize = data.size - headerSize

        // Extrair RSSI do header (offset 8, 1 byte signed)
        val rssi = if (data.size > 8) {
            data[8].toInt()  // RSSI em dBm (negativo)
        } else -50

        // Extrair canal do header (offset 9, 1 byte)
        val channel = if (data.size > 9) {
            data[9].toInt() and 0xFF
        } else 6

        // Extrair taxa (offset 10, 1 byte)
        val rate = if (data.size > 10) {
            data[10].toInt() and 0xFF
        } else 0

        // MAC address destino (offset 4 do frame 802.11)
        val macOffset = headerSize + 4
        val macAddress = if (data.size >= macOffset + 6) {
            data.copyOfRange(macOffset, macOffset + 6)
                .joinToString(":") { "%02x".format(it) }
        } else "00:00:00:00:00:00"

        // Tipo de frame (offset 0 do 802.11, bits 2-3)
        val frameControl = if (data.size > headerSize) {
            data[headerSize].toInt() and 0xFF
        } else 0
        val frameType = when ((frameControl shr 2) and 0x3) {
            0 -> "mgmt"
            1 -> "ctrl"
            2 -> "data"
            else -> "unknown"
        }

        return NexmonResult.Frame(
            timestampNs = System.nanoTime(),
            chipFamily = detectedChip,
            channel = channel,
            bandwidth = 20,
            rssi = rssi,
            macAddress = macAddress,
            frameType = frameType,
            rate = rate,
            rawData = data.copyOfRange(headerSize, data.size)
        )
    }

    // ─── Processamento de sinal ───

    private fun extractMetrics(rawData: ByteArray): FloatArray {
        // Extrair metricas do frame 802.11
        // Usar distribuicao de bytes como proxy para assinatura
        val bins = 5
        val profile = FloatArray(bins)
        val chunkSize = rawData.size / bins

        for (i in 0 until bins) {
            val start = i * chunkSize
            val end = min(start + chunkSize, rawData.size)
            var sum = 0f
            for (j in start until end) {
                sum += (rawData[j].toInt() and 0xFF) / 255f
            }
            profile[i] = sum / (end - start)
        }

        // Normalizar
        val max = profile.maxOrNull() ?: 1f
        return profile.map { it / max }.toFloatArray()
    }

    private fun correlateSignatures(a: FloatArray, b: FloatArray): Float {
        val meanA = a.average().toFloat()
        val meanB = b.average().toFloat()

        var numerator = 0f
        var denomA = 0f
        var denomB = 0f

        for (i in a.indices) {
            val diffA = a[i] - meanA
            val diffB = b[i] - meanB
            numerator += diffA * diffB
            denomA += diffA * diffA
            denomB += diffB * diffB
        }

        return if (denomA > 0 && denomB > 0) {
            numerator / sqrt(denomA * denomB)
        } else 0f
    }

    private fun estimateEnergyFromRSSI(rssi: Int, rate: Int): Double {
        // Energia estimada inversamente proporcional a RSSI
        // e proporcional a taxa de transmissao
        val baseEnergy = abs(rssi) * 100.0
        val rateFactor = if (rate > 0) rate / 54.0 else 1.0
        return baseEnergy * rateFactor
    }

    // ─── Utilitarios ───

    private fun activateNexmon(channel: Int, filter: String) {
        try {
            // Desativar WiFi do sistema
            Runtime.getRuntime().exec("su -c 'svc wifi disable'")
            Thread.sleep(500)

            // Ativar interface
            Runtime.getRuntime().exec("su -c 'ifconfig wlan0 up'")
            Thread.sleep(200)

            // Configurar modo monitor
            Runtime.getRuntime().exec("su -c 'nexutil -m1'")
            Runtime.getRuntime().exec("su -c 'nexutil -c$channel'")
            Runtime.getRuntime().exec("su -c 'nexutil -b$filter'")

            // Criar device node
            Runtime.getRuntime().exec("su -c 'mknod /dev/nexmon_csi c 243 0 2>/dev/null; chmod 666 /dev/nexmon_csi'")

        } catch (e: Exception) {
            Log.e("ArkheNexmon", "Falha ao ativar Nexmon: ${e.message}")
        }
    }

    private fun detectChipFamily(): String {
        return try {
            val process = Runtime.getRuntime().exec("su -c 'cat /data/local/tmp/nexmon_status.json 2>/dev/null || echo unknown'")
            val output = process.inputStream.bufferedReader().readText().trim()
            if (output != "unknown") {
                // Parse JSON simples
                val chipMatch = Regex("\"chip\":\"([^\"]+)\"").find(output)
                chipMatch?.groupValues?.get(1) ?: "unknown"
            } else {
                // Fallback: detectar via dmesg
                val dmesgProcess = Runtime.getRuntime().exec("su -c 'dmesg | grep -i brcm | head -1'")
                val dmesgOutput = dmesgProcess.inputStream.bufferedReader().readText()
                when {
                    dmesgOutput.contains("43430") -> "bcm43430a1"
                    dmesgOutput.contains("43455") -> "bcm43455c0"
                    dmesgOutput.contains("4358") -> "bcm4358"
                    dmesgOutput.contains("4375") -> "bcm4375b1"
                    else -> "unknown"
                }
            }
        } catch (e: Exception) {
            "unknown"
        }
    }

    private fun checkRootAccess(): Boolean {
        return try {
            val process = Runtime.getRuntime().exec("su -c 'id'")
            val output = process.inputStream.bufferedReader().readText()
            output.contains("uid=0")
        } catch (e: Exception) {
            false
        }
    }

    companion object {
        const val TAG = "ArkheNexmon"
        const val CHANNEL = "com.arkhe.citizen/nexmon"
    }
}

data class ParticleDetection(
    val particleType: String,
    val confidence: Float,
    val energyKeV: Double,
    val timestampNs: Long,
    val sourceFrame: NexmonResult.Frame
)

/**
 * Plugin Flutter para Nexmon CSI
 */
class NexmonFlutterPlugin {
    companion object {
        fun registerWith(engine: io.flutter.embedding.engine.FlutterEngine, context: Context) {
            val methodChannel = io.flutter.plugin.common.MethodChannel(
                engine.dartExecutor.binaryMessenger,
                NexmonCSIBridge.CHANNEL
            )
            val eventChannel = io.flutter.plugin.common.EventChannel(
                engine.dartExecutor.binaryMessenger,
                "${NexmonCSIBridge.CHANNEL}/stream"
            )

            val bridge = NexmonCSIBridge(context)

            methodChannel.setMethodCallHandler { call, result ->
                when (call.method) {
                    "checkPrerequisites" -> {
                        result.success(bridge.checkPrerequisites())
                    }
                    "startCapture" -> {
                        val channel = call.argument<Int>("channel") ?: 6
                        val bandwidth = call.argument<Int>("bandwidth") ?: 20
                        val filter = call.argument<String>("filter") ?: "0x88"

                        val res = bridge.startCapture(channel, bandwidth, filter)
                        when (res) {
                            is NexmonResult.Frame -> result.success(mapOf(
                                "status" to "started",
                                "chip" to res.chipFamily,
                                "channel" to res.channel
                            ))
                            NexmonResult.NotRooted -> result.error(
                                "NOT_ROOTED", "Dispositivo necessita root", null
                            )
                            NexmonResult.ModuleNotInstalled -> result.error(
                                "MODULE_NOT_INSTALLED",
                                "Instale o modulo Magisk nexmon_csi_arkhe",
                                mapOf("recoverable" to true)
                            )
                            is NexmonResult.Error -> result.error(
                                res.code.toString(), res.message,
                                mapOf("recoverable" to res.recoverable)
                            )
                            else -> result.error("UNKNOWN", "Erro desconhecido", null)
                        }
                    }
                    "stopCapture" -> {
                        bridge.stopCapture()
                        result.success(mapOf("status" to "stopped"))
                    }
                    "getChipInfo" -> {
                        result.success(mapOf(
                            "chipFamily" to bridge.checkPrerequisites()["chipFamily"],
                            "detected" to (bridge.checkPrerequisites()["chipFamily"] != "unknown")
                        ))
                    }
                    else -> result.notImplemented()
                }
            }

            eventChannel.setStreamHandler(object : io.flutter.plugin.common.EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: io.flutter.plugin.common.EventChannel.EventSink?) {
                    CoroutineScope(Dispatchers.Main).launch {
                        bridge.frameFlow.collect { frame ->
                            events?.success(mapOf(
                                "timestampNs" to frame.timestampNs,
                                "chipFamily" to frame.chipFamily,
                                "channel" to frame.channel,
                                "rssi" to frame.rssi,
                                "macAddress" to frame.macAddress,
                                "frameType" to frame.frameType,
                                "rate" to frame.rate,
                                "rawDataLength" to frame.rawData.size
                            ))
                        }
                    }
                }
                override fun onCancel(arguments: Any?) {}
            })
        }
    }
}