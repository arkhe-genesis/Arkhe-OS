// KYM/StrongBoxManager.kt
// Nexus Android — Gerenciamento seguro de chaves via Android StrongBox

package os.arkhe.nexus.KYM

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.Signature
import javax.crypto.Cipher

class StrongBoxManager {
    companion object {
        private const val KEY_ALIAS = "arkhe_nexus_kym_key"
        private const val KEYSTORE_PROVIDER = "AndroidKeyStore"
    }

    private val keyStore: KeyStore = KeyStore.getInstance(KEYSTORE_PROVIDER).apply {
        load(null)
    }

    /// Gera par de chaves Ed25519 no StrongBox (se disponível)
    suspend fun generateKeyPair(): ByteArray {
        // Verificar suporte a StrongBox
        val hasStrongBox = android.security.keystore.KeyProperties.KEYSTORE_NAME_ANDROID_STRONGBOX in
            KeyStore.getInstance("AndroidKeyStore").providers.map { it.name }

        val keySpec = KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        ).apply {
            setAlgorithmParameterSpec(
                java.security.spec.ECGenParameterSpec("secp256r1")
            )
            setDigests(KeyProperties.DIGEST_SHA256)
            setUserAuthenticationRequired(true)
            setUserAuthenticationValidityDurationSeconds(30)

            // Usar StrongBox se disponível
            if (hasStrongBox) {
                setIsStrongBoxBacked(true)
            }

            // Requer biometria ou PIN
            setUserAuthenticationParameters(
                30,
                KeyProperties.AUTH_BIOMETRIC_STRONG or KeyProperties.AUTH_DEVICE_CREDENTIAL
            )
        }.build()

        val keyPairGenerator = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_EC, KEYSTORE_PROVIDER
        )
        keyPairGenerator.initialize(keySpec)
        return keyPairGenerator.generateKeyPair().public.encoded
    }

    /// Assina desafio KYM usando chave no StrongBox
    suspend fun signChallenge(challenge: ByteArray): ByteArray {
        val privateKey = keyStore.getKey(KEY_ALIAS, null) as? java.security.PrivateKey
            ?: throw IllegalStateException("Chave não encontrada no StrongBox")

        val signature = Signature.getInstance("SHA256withECDSA")
        signature.initSign(privateKey)
        signature.update(challenge)

        return signature.sign()
    }

    /// Verifica integridade do dispositivo (root detection)
    fun verifyDeviceIntegrity(): Boolean {
        return !checkRootMethods() && !checkSuBinary() && !checkBuildTags()
    }

    private fun checkRootMethods(): Boolean {
        return try {
            Runtime.getRuntime().exec("su")
            true
        } catch (e: Exception) {
            false
        }
    }

    private fun checkSuBinary(): Boolean {
        val paths = arrayOf(
            "/sbin/su", "/system/bin/su", "/system/xbin/su",
            "/data/local/xbin/su", "/data/local/bin/su"
        )
        return paths.any { java.io.File(it).exists() }
    }

    private fun checkBuildTags(): Boolean {
        return android.os.Build.TAGS?.contains("test-keys") == true
    }
}