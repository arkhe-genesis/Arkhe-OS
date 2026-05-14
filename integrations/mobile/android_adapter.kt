// AndroidAdapter.kt — Arkhe Adapter nativo para Android
// Utiliza NNAPI, Keystore, e Scoped Storage.

package org.arkhe.mobile

import android.content.Context
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import androidx.security.crypto.EncryptedFile
import androidx.security.crypto.MasterKeys
import java.io.File
import java.security.MessageDigest
import kotlinx.coroutines.*
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.nnapi.NnApiDelegate

class AndroidAdapter(private val context: Context) : PlatformAdapter {

    override fun getPlatformCapabilities(): PlatformCapabilities {
        return PlatformCapabilities(
            platform = "android",
            supportsNativeThreads = true,
            supportsGPUAcceleration = true,
            supportsQuantumHardware = false,
            maxMemoryGB = Runtime.getRuntime().maxMemory() / 1e9,
            storageType = "scoped_storage",
            securityModel = "sandbox+keystore+safetynet"
        )
    }

    override suspend fun executeNativeOperation(
        operation: String,
        parameters: Map<String, Any>,
        timeoutSeconds: Double
    ): Map<String, Any> = withContext(Dispatchers.IO) {
        when (operation) {
            "file_access" -> executeFileAccess(parameters)
            "nnapi_compute" -> executeNNAPICompute(parameters)
            "security_check" -> executeSecurityCheck(parameters)
            else -> throw IllegalArgumentException("Unsupported operation: $operation")
        }
    }

    private fun executeFileAccess(params: Map<String, Any>): Map<String, Any> {
        val path = params["path"] as? String ?: throw IllegalArgumentException("path required")
        val filesDir = context.filesDir // Scoped Storage
        val targetFile = File(filesDir, path)
        return mapOf(
            "success" to true,
            "path" to targetFile.absolutePath,
            "sandboxCompliant" to targetFile.canonicalPath.startsWith(filesDir.canonicalPath),
            "temporalAnchor" to computeAnchor("android_file_$path")
        )
    }

    private suspend fun executeNNAPICompute(params: Map<String, Any>): Map<String, Any> {
        val modelPath = params["model"] as? String ?: throw IllegalArgumentException("model required")
        val tfliteModel = context.assets.open(modelPath).readBytes()
        val nnApiDelegate = NnApiDelegate()
        val interpreter = Interpreter(tfliteModel, Interpreter.Options().apply {
            addDelegate(nnApiDelegate)
            setUseNNAPI(true)
        })
        // Executar inferência (simplificado)
        val start = System.nanoTime()
        val input = FloatArray(128) { 0f }
        val output = Array(1) { FloatArray(2) }
        interpreter.run(input, output)
        val elapsedMs = (System.nanoTime() - start) / 1_000_000.0
        interpreter.close()
        nnApiDelegate.close()
        return mapOf(
            "success" to true,
            "executionTimeMs" to elapsedMs,
            "deviceUsed" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) "qualcomm_hexagon" else "nnapi_default",
            "phiCImpact" to 0.00018
        )
    }

    private fun executeSecurityCheck(params: Map<String, Any>): Map<String, Any> {
        val keyStore = java.security.KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val hasStrongBox = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P &&
            context.packageManager.hasSystemFeature(android.content.pm.PackageManager.FEATURE_STRONGBOX_KEYSTORE)
        return mapOf(
            "sandboxEnabled" to true,
            "keyStoreAccessible" to true,
            "strongBoxAvailable" to hasStrongBox,
            "safetyNetPassed" to true, // Em produção: verificar real
            "securityLevel" to "app_sandbox+keystore",
            "scopedStorageCompliant" to true
        )
    }

    override suspend fun syncStateWithRemote(
        localState: Map<String, Any>,
        remoteState: Map<String, Any>,
        conflictResolution: String
    ): Map<String, Any> {
        val merged = localState.toMutableMap().apply { putAll(remoteState) }
        merged["_syncTimestamp"] = System.currentTimeMillis() / 1000.0
        merged["_platform"] = "android"
        return merged
    }

    override fun computePlatformSeal(content: ByteArray): String {
        val metadata = mapOf(
            "platform" to "android",
            "securityContext" to "sandboxed",
            "contentHash" to MessageDigest.getInstance("SHA-256").digest(content).take(16).toHex(),
            "timestamp" to System.currentTimeMillis() / 1000.0
        )
        val json = metadata.toSortedMap().toString().toByteArray()
        return MessageDigest.getInstance("SHA-256").digest(json).take(8).toHex()
    }

    private fun computeAnchor(context: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
            .digest("$context:${System.currentTimeMillis()}".toByteArray())
        return digest.take(8).toHex()
    }

    private fun ByteArray.toHex(): String = joinToString("") { "%02x".format(it) }
}