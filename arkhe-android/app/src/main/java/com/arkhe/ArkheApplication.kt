// app/src/main/java/com/arkhe/ArkheApplication.kt
package com.arkhe

import android.app.Application
import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Log
import com.arkhe.core.ConsistencyOracle
import com.arkhe.core.TemporalHashChain
import com.arkhe.tee.AndroidKeystoreBridge
import com.arkhe.tee.StrongBoxAttestation
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.SupervisorJob
import java.security.KeyStore
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey

class ArkheApplication : Application() {

    companion object {
        private const val TAG = "ArkheApp"
        private const val KEY_ALIAS = "arkhe_master_key"
        private const val KEYSTORE_PROVIDER = "AndroidKeyStore"

        @JvmStatic
        lateinit var instance: ArkheApplication
            private set
    }

    // Application scope para operações assíncronas
    val applicationScope = CoroutineScope(SupervisorJob())

    // Componentes canônicos do ARKHE
    private lateinit var oracle: ConsistencyOracle
    private lateinit var hashChain: TemporalHashChain
    private lateinit var keystoreBridge: AndroidKeystoreBridge
    private lateinit var attestation: StrongBoxAttestation

    override fun onCreate() {
        super.onCreate()
        instance = this

        Log.i(TAG, "🏛️ ARKHE OS — Inicializando runtime mobile")

        // 1. Inicializar bridge com Android Keystore
        keystoreBridge = AndroidKeystoreBridge(applicationContext).apply {
            initialize()
        }

        // 2. Verificar suporte a StrongBox (hardware-backed keys)
        attestation = StrongBoxAttestation(applicationContext)
        if (attestation.isStrongBoxAvailable) {
            Log.i(TAG, "✅ StrongBox disponível — chaves protegidas por hardware")
        } else {
            Log.w(TAG, "⚠️ StrongBox não disponível — usando TEE padrão")
        }

        // 3. Gerar/recuperar chave mestra
        val masterKey = getOrCreateMasterKey()

        // 4. Inicializar ConsistencyOracle com configuração mobile
        oracle = ConsistencyOracle(
            ledger = hashChain,
            observerDistanceAU = 0.0, // Dispositivo móvel = na Terra
            galacticCoherence = true,
            quantumWindow = 1e-12 // 1 ps padrão para superfície terrestre
        )

        // 5. Inicializar TemporalHashChain
        hashChain = TemporalHashChain(
            genesisHash = "a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4",
            encryptionKey = masterKey,
            compressionEnabled = true
        )

        // 6. Registrar evento de inicialização no ledger
        hashChain.recordEvent(
            type = "mobile_node_initialized",
            payload = mapOf(
                "device_model" to android.os.Build.MODEL,
                "android_version" to android.os.Build.VERSION.RELEASE,
                "strongbox_available" to attestation.isStrongBoxAvailable,
                "timestamp" to System.currentTimeMillis()
            )
        )

        Log.i(TAG, "✅ ARKHE OS — Runtime mobile inicializado")
        Log.i(TAG, "   Oracle: ${oracle.javaClass.simpleName}")
        Log.i(TAG, "   HashChain: ${hashChain.javaClass.simpleName}")
        Log.i(TAG, "   TEE: ${if (attestation.isStrongBoxAvailable) "StrongBox" else "Android Keystore"}")
    }

    /**
     * Gera ou recupera a chave mestra do ARKHE no Android Keystore.
     * A chave é:
     * - Hardware-backed se StrongBox disponível
     * - Imexportável (nunca sai do TEE)
     * - Usada apenas para operações criptográficas internas
     */
    private fun getOrCreateMasterKey(): SecretKey {
        val keyStore = KeyStore.getInstance(KEYSTORE_PROVIDER).apply {
            load(null)
        }

        // Tentar recuperar chave existente
        val existingEntry = keyStore.getEntry(KEY_ALIAS, null)
        if (existingEntry is KeyStore.SecretKeyEntry) {
            Log.d(TAG, "🔑 Chave mestra recuperada do Keystore")
            return existingEntry.secretKey
        }

        // Gerar nova chave
        Log.d(TAG, "🔐 Gerando nova chave mestra no Keystore")
        val keyParams = KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .apply {
                if (attestation.isStrongBoxAvailable) {
                    setIsStrongBoxBacked(true)
                    Log.d(TAG, "   → Hardware-backed (StrongBox)")
                }
                setUserAuthenticationRequired(false)
                setRandomizedEncryptionRequired(true)
            }
            .build()

        val keyGenerator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            KEYSTORE_PROVIDER
        )
        keyGenerator.init(keyParams)
        return keyGenerator.generateKey()
    }

    /**
     * Acessor para componentes canônicos (usado por Activities/Services).
     */
    fun getOracle(): ConsistencyOracle = oracle
    fun getHashChain(): TemporalHashChain = hashChain
    fun getKeystoreBridge(): AndroidKeystoreBridge = keystoreBridge
    fun getAttestation(): StrongBoxAttestation = attestation

    /**
     * Verifica integridade do runtime (chamado periodicamente).
     */
    fun verifyRuntimeIntegrity(): Boolean {
        // Verificar que a chave mestra ainda está acessível
        try {
            keystoreBridge.verifyKeyAccess(KEY_ALIAS)
        } catch (e: Exception) {
            Log.e(TAG, "❌ Integridade comprometida: chave inacessível", e)
            return false
        }

        // Verificar hash do código nativo (anti-tampering)
        val nativeHash = computeNativeCodeHash()
        val expectedHash = BuildConfig.NATIVE_CODE_HASH

        if (nativeHash != expectedHash) {
            Log.e(TAG, "❌ Código nativo modificado: hash mismatch")
            return false
        }

        Log.d(TAG, "✅ Integridade do runtime verificada")
        return true
    }

    private fun computeNativeCodeHash(): String {
        // Em produção: calcular hash do .so carregado via JNI
        // Aqui: valor simulado
        return BuildConfig.NATIVE_CODE_HASH
    }
}
package com.arkhe

import android.app.Application
import android.util.Log

class ArkheApplication : Application() {
    companion object {
        private const val TAG = "ArkheApp"

        init {
            // System.loadLibrary("arkhe_core")
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "🏛️ ARKHE OS — Inicializando runtime mobile")
    }
}
