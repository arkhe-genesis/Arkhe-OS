package com.arkhe.citizen.detector.csi

import android.content.Context
import android.net.wifi.WifiManager
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.io.*
import java.net.*
import kotlin.math.*
import java.util.Random

/**
 * ARKHE OS — Substrato 406-WIFI-CSI-ROOT
 * Bridge nativa para extração de CSI (Channel State Information) em dispositivos rootados
 * Suporta: ath10k (QCA6174), bcm4358, iwlwifi (Intel)
 *
 * Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
 * Requisitos: ROOT + kernel modificado com CSI logging habilitado
 *             ou driver modificado (ath10k-CSI, nexmon)
 */

sealed class CSIResult {
    data class Frame(
        val timestampNs: Long,
        val deviceType: String,  // "ath10k", "bcm4358", "iwlwifi"
        val channel: Int,
        val bandwidth: Int,  // 20, 40, 80 MHz
        val subcarriers: Int,
        val csiData: FloatArray,  // Amplitude/phase por subportadora
        val rssi: Int,
        val macAddress: String,
        val frameType: String  // "data", "mgmt", "ctrl"
    ) : CSIResult() {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false
            other as Frame
            return timestampNs == other.timestampNs
        }
        override fun hashCode(): Int = timestampNs.hashCode()
    }

    data class Error(
        val code: Int,
        val message: String,
        val requiresRoot: Boolean
    ) : CSIResult()

    object RootRequired : CSIResult()
    object DriverNotFound : CSIResult()
}

enum class CSIDevice(val driverPath: String, val extractorScript: String) {
    ATH10K_QCA6174(
        "/sys/kernel/debug/ath10k/pci0000:01:00.0/spectral_scan_ctl",
        "extract_ath10k_csi.sh"
    ),
    BCM4358_NEXMON(
        "/dev/nexmon_csi",
        "extract_nexmon_csi.sh"
    ),
    IWLWIFI_8265(
        "/sys/kernel/debug/iwlwifi/0000:02:00.0/iwlmvm/sfcs_debug",
        "extract_iwlwifi_csi.sh"
    );

    companion object {
        fun detectDevice(): CSIDevice? {
            return values().firstOrNull {
                File(it.driverPath).exists()
            }
        }
    }
}

class ArkheCSIBridge(private val context: Context) {

    private val wifiManager = context.getSystemService(Context.WIFI_SERVICE) as? WifiManager
    private val _csiFlow = MutableSharedFlow<CSIResult.Frame>(extraBufferCapacity = 100)
    val csiFlow: SharedFlow<CSIResult.Frame> = _csiFlow.asSharedFlow()

    private var detectionJob: Job? = null
    private var isRunning = false
    private var detectedDevice: CSIDevice? = null

    // Configuração de deteção de partículas via CSI
    private val csiThreshold = 3.0f  // desvio padrão mínimo
    private val particleSignatures = mapOf(
        "muon" to floatArrayOf(0.8f, 0.6f, 0.4f, 0.3f, 0.2f),  // decaimento exponencial
        "electron" to floatArrayOf(0.5f, 0.7f, 0.5f, 0.3f, 0.1f),  // pico central
        "photon" to floatArrayOf(0.3f, 0.4f, 0.5f, 0.4f, 0.3f),  // distribuição gaussiana
    )

    /**
     * Verifica se o dispositivo tem acesso root e driver CSI disponível
     */
    fun checkPrerequisites(): Map<String, Any> {
        val hasRoot = checkRootAccess()
        val device = CSIDevice.detectDevice()

        return mapOf(
            "hasRoot" to hasRoot,
            "deviceSupported" to (device != null),
            "deviceType" to (device?.name ?: "NONE"),
            "driverPath" to (device?.driverPath ?: "N/A"),
            "ready" to (hasRoot && device != null)
        )
    }

    private fun enableMonitorMode() {
        try {
            // Activating monitor mode (Broadcom + Nexmon) using su
            val process = Runtime.getRuntime().exec(arrayOf("su", "-c", "svc wifi disable; ifconfig wlan0 up; nexutil -s0x613 -i -v2"))
            process.waitFor()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to enable monitor mode: ${e.message}")
        }
    }

    /**
     * Inicia captura de CSI em tempo real
     */
    fun startCapture(sampleRateHz: Int = 100): CSIResult {
        val prereqs = checkPrerequisites()

        if (!(prereqs["hasRoot"] as Boolean)) {
            return CSIResult.RootRequired
        }

        detectedDevice = CSIDevice.detectDevice()
        if (detectedDevice == null) {
            return CSIResult.DriverNotFound
        }

        enableMonitorMode()

        isRunning = true

        detectionJob = CoroutineScope(Dispatchers.IO).launch {
            when (detectedDevice) {
                CSIDevice.ATH10K_QCA6174 -> captureAth10k(sampleRateHz)
                CSIDevice.BCM4358_NEXMON -> captureNexmon(sampleRateHz)
                CSIDevice.IWLWIFI_8265 -> captureIwlwifi(sampleRateHz)
                else -> { }
            }
        }

        return CSIResult.Frame(
            timestampNs = System.nanoTime(),
            deviceType = detectedDevice!!.name,
            channel = wifiManager?.connectionInfo?.frequency ?: 0,
            bandwidth = 80,
            subcarriers = 234,
            csiData = FloatArray(234) { 0f },
            rssi = -50,
            macAddress = "00:00:00:00:00:00",
            frameType = "init"
        )
    }

    fun stopCapture() {
        isRunning = false
        detectionJob?.cancel()
        detectionJob = null
    }

    /**
     * Processa frame CSI para deteção de partículas
     * Algoritmo: compara assinatura do frame com padrões conhecidos de partículas
     */
    fun processFrameForParticles(frame: CSIResult.Frame): ParticleDetection? {
        val amplitudeProfile = extractAmplitudeProfile(frame.csiData)

        // Correlacionar com assinaturas conhecidas
        var bestMatch = "unknown"
        var bestScore = 0.0f

        for ((particle, signature) in particleSignatures) {
            val score = correlateProfiles(amplitudeProfile, signature)
            if (score > bestScore && score > 0.7f) {
                bestScore = score
                bestMatch = particle
            }
        }

        if (bestMatch == "unknown") return null

        return ParticleDetection(
            particleType = bestMatch,
            confidence = bestScore,
            energyKeV = estimateEnergy(frame.csiData),
            timestampNs = frame.timestampNs,
            csiFrame = frame
        )
    }

    // ─── Captura específica por driver ───

    private suspend fun captureAth10k(sampleRateHz: Int) {
        // ath10k: ler de /sys/kernel/debug/ath10k/.../spectral_scan_ctl
        // e /sys/kernel/debug/ath10k/.../spectral_scan_bin
        val spectralCtl = File("/sys/kernel/debug/ath10k/pci0000:01:00.0/spectral_scan_ctl")
        val spectralBin = File("/sys/kernel/debug/ath10k/pci0000:01:00.0/spectral_scan_bin")

        // Ativar spectral scan
        try {
            val process = Runtime.getRuntime().exec(arrayOf("su", "-c", "echo trigger > ${spectralCtl.absolutePath}; echo chancorr > ${spectralCtl.absolutePath}"))
            process.waitFor()
        } catch (e: Exception) {
             Log.e(TAG, "Failed to configure ath10k: ${e.message}")
        }

        while (isRunning) {
            try {
                if (spectralBin.exists() && spectralBin.length() > 0) {
                    val process = Runtime.getRuntime().exec(arrayOf("su", "-c", "cat ${spectralBin.absolutePath}"))
                    val inputStream = process.inputStream
                    val data = inputStream.readBytes()

                    if (data.isNotEmpty()) {
                        val frame = parseAth10kCSI(data)
                        _csiFlow.emit(frame)
                    }

                    // Limpar buffer
                    Runtime.getRuntime().exec(arrayOf("su", "-c", "echo clear > ${spectralCtl.absolutePath}"))
                }
                delay((1000 / sampleRateHz).toLong())
            } catch (e: Exception) {
                Log.e("ArkheCSI", "Erro na captura ath10k: ${e.message}")
            }
        }
    }

    private suspend fun captureNexmon(sampleRateHz: Int) {
        // Nexmon: ler de /dev/nexmon_csi (character device)
        val nexmonDev = File("/dev/nexmon_csi")

        while (isRunning) {
            try {
                if (nexmonDev.exists()) {
                    val process = Runtime.getRuntime().exec(arrayOf("su", "-c", "cat ${nexmonDev.absolutePath} | head -c 4096"))
                    val inputStream = process.inputStream
                    val data = inputStream.readBytes()

                    if (data.isNotEmpty()) {
                        val frame = parseNexmonCSI(data)
                        _csiFlow.emit(frame)
                    }
                }
                delay((1000 / sampleRateHz).toLong())
            } catch (e: Exception) {
                Log.e("ArkheCSI", "Erro na captura nexmon: ${e.message}")
            }
        }
    }

    private suspend fun captureIwlwifi(sampleRateHz: Int) {
        // iwlwifi: usar debugfs para extrair CSI de frames recebidos
        val sfcsDebug = File("/sys/kernel/debug/iwlwifi/0000:02:00.0/iwlmvm/sfcs_debug")

        while (isRunning) {
            try {
                if (sfcsDebug.exists()) {
                    val process = Runtime.getRuntime().exec(arrayOf("su", "-c", "cat ${sfcsDebug.absolutePath}"))
                    val data = process.inputStream.bufferedReader().readText()

                    if (data.isNotEmpty()) {
                        val frame = parseIwlwifiCSI(data)
                        _csiFlow.emit(frame)
                    }
                }
                delay((1000 / sampleRateHz).toLong())
            } catch (e: Exception) {
                Log.e("ArkheCSI", "Erro na captura iwlwifi: ${e.message}")
            }
        }
    }

    // ─── Parsing de CSI ───

    private fun parseAth10kCSI(data: ByteArray): CSIResult.Frame {
        // Formato ath10k spectral scan: header + subcarrier data
        // Simplificação: extrair amplitude de cada subportadora
        val subcarriers = min(234, (data.size - 20) / 2)
        val csiData = FloatArray(subcarriers)

        for (i in 0 until subcarriers) {
            val offset = 20 + i * 2
            if (offset + 1 < data.size) {
                val raw = (data[offset].toInt() and 0xFF) or
                         ((data[offset + 1].toInt() and 0xFF) shl 8)
                csiData[i] = raw.toFloat() / 1000f  // Normalizar
            }
        }

        return CSIResult.Frame(
            timestampNs = System.nanoTime(),
            deviceType = "ath10k",
            channel = wifiManager?.connectionInfo?.frequency ?: 5180,
            bandwidth = 80,
            subcarriers = subcarriers,
            csiData = csiData,
            rssi = -50 - Random().nextInt(20),
            macAddress = "aa:bb:cc:dd:ee:ff",
            frameType = "data"
        )
    }

    private fun parseNexmonCSI(data: ByteArray): CSIResult.Frame {
        // Formato Nexmon: header (12 bytes) + CSI data
        val csiData = FloatArray(64)  // 64 subportadoras para 20MHz

        for (i in 0 until 64) {
            val offset = 12 + i * 4
            if (offset + 3 < data.size) {
                val real = (data[offset].toInt() and 0xFF) or
                          ((data[offset + 1].toInt() and 0xFF) shl 8)
                val imag = (data[offset + 2].toInt() and 0xFF) or
                          ((data[offset + 3].toInt() and 0xFF) shl 8)
                csiData[i] = sqrt((real * real + imag * imag).toFloat())
            }
        }

        return CSIResult.Frame(
            timestampNs = System.nanoTime(),
            deviceType = "bcm4358",
            channel = 2437,
            bandwidth = 20,
            subcarriers = 64,
            csiData = csiData,
            rssi = -45,
            macAddress = "11:22:33:44:55:66",
            frameType = "data"
        )
    }

    private fun parseIwlwifiCSI(data: String): CSIResult.Frame {
        // iwlwifi debugfs: formato texto
        val lines = data.lines()
        val csiData = FloatArray(52)  // 52 subportadoras para 20MHz

        lines.forEachIndexed { index, line ->
            if (index < 52) {
                csiData[index] = line.toFloatOrNull() ?: 0f
            }
        }

        return CSIResult.Frame(
            timestampNs = System.nanoTime(),
            deviceType = "iwlwifi",
            channel = 2412,
            bandwidth = 20,
            subcarriers = 52,
            csiData = csiData,
            rssi = -55,
            macAddress = "77:88:99:aa:bb:cc",
            frameType = "mgmt"
        )
    }

    // ─── Processamento de sinal ───

    private fun extractAmplitudeProfile(csiData: FloatArray): FloatArray {
        val profileSize = 5
        val profile = FloatArray(profileSize)
        val chunkSize = csiData.size / profileSize

        for (i in 0 until profileSize) {
            val start = i * chunkSize
            val end = min(start + chunkSize, csiData.size)
            var sum = 0f
            for (j in start until end) {
                sum += csiData[j]
            }
            profile[i] = sum / (end - start)
        }

        // Normalizar
        val max = profile.maxOrNull() ?: 1f
        return profile.map { it / max }.toFloatArray()
    }

    private fun correlateProfiles(a: FloatArray, b: FloatArray): Float {
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

    private fun estimateEnergy(csiData: FloatArray): Double {
        // Energia proporcional à soma das amplitudes ao quadrado
        val totalEnergy = csiData.sumOf { (it * it).toDouble() }
        return totalEnergy * 10.0  // Fator de calibração aproximado
    }

    // ─── Utilitários ───

    private fun checkRootAccess(): Boolean {
        return try {
            val process = Runtime.getRuntime().exec(arrayOf("su", "-c", "id"))
            val output = process.inputStream.bufferedReader().readText()
            output.contains("uid=0")
        } catch (e: Exception) {
            false
        }
    }

    companion object {
        const val TAG = "ArkheCSI"
        const val CHANNEL = "com.arkhe.citizen/csi"
    }
}

data class ParticleDetection(
    val particleType: String,
    val confidence: Float,
    val energyKeV: Double,
    val timestampNs: Long,
    val csiFrame: CSIResult.Frame
)

/**
 * Bridge Flutter para CSI
 */
class ArkheCSIPlugin {
    companion object {
        fun registerWith(registrar: io.flutter.plugin.common.PluginRegistry.Registrar) {
            val channel = io.flutter.plugin.common.MethodChannel(registrar.messenger(), ArkheCSIBridge.CHANNEL)
            val bridge = ArkheCSIBridge(registrar.context())

            channel.setMethodCallHandler { call, result ->
                when (call.method) {
                    "checkPrerequisites" -> {
                        result.success(bridge.checkPrerequisites())
                    }
                    "startCapture" -> {
                        val sampleRate = call.argument<Int>("sampleRateHz") ?: 100
                        val res = bridge.startCapture(sampleRate)
                        when (res) {
                            is CSIResult.Frame -> result.success(mapOf(
                                "status" to "started",
                                "device" to res.deviceType,
                                "channel" to res.channel
                            ))
                            is CSIResult.RootRequired -> result.error(
                                "ROOT_REQUIRED", "Dispositivo necessita root", null
                            )
                            is CSIResult.DriverNotFound -> result.error(
                                "DRIVER_NOT_FOUND", "Driver CSI não encontrado", null
                            )
                            else -> result.error("UNKNOWN", "Erro desconhecido", null)
                        }
                    }
                    "stopCapture" -> {
                        bridge.stopCapture()
                        result.success(mapOf("status" to "stopped"))
                    }
                    else -> result.notImplemented()
                }
            }

            // Event channel para streaming de CSI em tempo real
            val eventChannel = io.flutter.plugin.common.EventChannel(registrar.messenger(), "${ArkheCSIBridge.CHANNEL}/stream")
            eventChannel.setStreamHandler(object : io.flutter.plugin.common.EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: io.flutter.plugin.common.EventChannel.EventSink?) {
                    CoroutineScope(Dispatchers.Main).launch {
                        bridge.csiFlow.collect { frame ->
                            events?.success(mapOf(
                                "timestampNs" to frame.timestampNs,
                                "deviceType" to frame.deviceType,
                                "channel" to frame.channel,
                                "subcarriers" to frame.subcarriers,
                                "rssi" to frame.rssi,
                                "csiData" to frame.csiData.toList()
                            ))
                        }
                    }
                }
                override fun onCancel(arguments: Any?) {}
            })
        }
    }
}
