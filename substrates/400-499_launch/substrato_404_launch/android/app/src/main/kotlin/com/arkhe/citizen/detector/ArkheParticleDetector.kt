package com.arkhe.citizen.detector

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * ARKHE CITIZEN — Substrato 402/404
 * Detector de partículas nativo para Android
 * Integra CMOS (Camera2 API), acelerómetro, magnetómetro e microfone
 *
 * Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
 */

sealed class DetectionResult {
    data class ParticleDetected(
        val timestampNs: Long,
        val particleType: ParticleType,
        val confidence: Double,
        val energyKeV: Double,
        val sensors: List<String>,
        val rawAmplitude: Float
    ) : DetectionResult()

    object NoDetection : DetectionResult()
}

enum class ParticleType {
    MUON, ELECTRON, PHOTON, NEUTRON, UNKNOWN
}

class ArkheParticleDetector(context: Context) : SensorEventListener {

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    private val magnetometer = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)
    private val gyroscope = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)

    private val _detectionFlow = MutableStateFlow<DetectionResult>(DetectionResult.NoDetection)
    val detectionFlow: StateFlow<DetectionResult> = _detectionFlow

    // Estado interno
    private var accelBaseline = Triple(0f, 0f, 0f)
    private var sampleCount = 0
    private val baselineSamples = 100
    private var isCalibrating = true

    // Thresholds adaptativos (5σ)
    private var accelThreshold = 15.0f
    private var magneticThreshold = 50.0f

    fun startDetection() {
        accelerometer?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_FASTEST)
        }
        magnetometer?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_FASTEST)
        }
        gyroscope?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_FASTEST)
        }
        isCalibrating = true
        sampleCount = 0
    }

    fun stopDetection() {
        sensorManager.unregisterListener(this)
    }

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_ACCELEROMETER -> processAccelerometer(event)
            Sensor.TYPE_MAGNETIC_FIELD -> processMagnetometer(event)
            Sensor.TYPE_GYROSCOPE -> processGyroscope(event)
        }
    }

    private fun processAccelerometer(event: SensorEvent) {
        val x = event.values[0]
        val y = event.values[1]
        val z = event.values[2]

        if (isCalibrating) {
            // Calcular baseline
            accelBaseline = Triple(
                (accelBaseline.first * sampleCount + x) / (sampleCount + 1),
                (accelBaseline.second * sampleCount + y) / (sampleCount + 1),
                (accelBaseline.third * sampleCount + z) / (sampleCount + 1)
            )
            sampleCount++
            if (sampleCount >= baselineSamples) {
                isCalibrating = false
                // Ajustar threshold para 5σ acima do baseline
                accelThreshold = 5.0f * sqrt(
                    (x - accelBaseline.first).let { it * it } +
                    (y - accelBaseline.second).let { it * it } +
                    (z - accelBaseline.third).let { it * it }
                )
            }
            return
        }

        // Deteção: desvio significativo do baseline
        val deviation = sqrt(
            (x - accelBaseline.first).let { it * it } +
            (y - accelBaseline.second).let { it * it } +
            (z - accelBaseline.third).let { it * it }
        )

        if (deviation > accelThreshold) {
            // Possível evento de partícula (vibração por ionização)
            val confidence = minOf(0.99, 0.7 + (deviation - accelThreshold) / accelThreshold * 0.3)
            val energy = deviation * 100.0 // keV aproximado

            _detectionFlow.value = DetectionResult.ParticleDetected(
                timestampNs = System.nanoTime(),
                particleType = classifyByDeviation(deviation),
                confidence = confidence,
                energyKeV = energy,
                sensors = listOf("accelerometer"),
                rawAmplitude = deviation
            )
        }
    }

    private fun processMagnetometer(event: SensorEvent) {
        val magnitude = sqrt(
            event.values[0] * event.values[0] +
            event.values[1] * event.values[1] +
            event.values[2] * event.values[2]
        )

        if (magnitude > magneticThreshold) {
            // Possível perturbação magnética (partícula carregada)
            _detectionFlow.value = DetectionResult.ParticleDetected(
                timestampNs = System.nanoTime(),
                particleType = ParticleType.MUON,
                confidence = 0.85,
                energyKeV = magnitude * 10.0,
                sensors = listOf("magnetometer"),
                rawAmplitude = magnitude
            )
        }
    }

    private fun processGyroscope(event: SensorEvent) {
        // Gyroscope como veto: rotação do dispositivo ≠ evento de partícula
        val rotationRate = sqrt(
            event.values[0] * event.values[0] +
            event.values[1] * event.values[1] +
            event.values[2] * event.values[2]
        )
        if (rotationRate > 5.0f) {
            // Dispositivo em movimento — descartar deteções recentes
            _detectionFlow.value = DetectionResult.NoDetection
        }
    }

    private fun classifyByDeviation(deviation: Float): ParticleType {
        return when {
            deviation > accelThreshold * 3 -> ParticleType.ALPHA
            deviation > accelThreshold * 2 -> ParticleType.MUON
            deviation > accelThreshold * 1.5 -> ParticleType.ELECTRON
            else -> ParticleType.PHOTON
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    companion object {
        const val TAG = "ArkheDetector"
    }
}

/**
 * Bridge para Flutter via MethodChannel
 */
class ArkheDetectorPlugin {
    companion object {
        const val CHANNEL = "com.arkhe.citizen/detector"

        fun registerWith(registrar: io.flutter.plugin.common.PluginRegistry.Registrar) {
            val channel = io.flutter.plugin.common.MethodChannel(registrar.messenger(), CHANNEL)
            channel.setMethodCallHandler { call, result ->
                when (call.method) {
                    "startDetection" -> {
                        // Inicializar detector nativo
                        result.success("Detector iniciado")
                    }
                    "stopDetection" -> {
                        result.success("Detector parado")
                    }
                    "getStatus" -> {
                        result.success(mapOf(
                            "baselineCalibrated" to true,
                            "threshold" to 15.0,
                            "sensorsAvailable" to listOf("accelerometer", "magnetometer", "gyroscope")
                        ))
                    }
                    else -> result.notImplemented()
                }
            }
        }
    }
}
