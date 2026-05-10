// app/src/main/jni/crypto_falcon.cpp
#include <jni.h>
#include <android/log.h>
#include <oqs/oqs.h>
#include <cstring>
#include <cstdlib>

#define TAG "ArkheNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

// Constantes do Falcon-1024 (ML-DSA-1024)
static const size_t FALCON_PK_SIZE = 1792;   // Chave pública
static const size_t FALCON_SK_SIZE = 3584;   // Chave secreta
static const size_t FALCON_SIG_SIZE = 1280;  // Assinatura

extern "C" {

// JNI: Gerar par de chaves Falcon-1024
JNIEXPORT jbyteArray JNICALL
Java_com_arkhe_core_crypto_Falcon1024_nativeKeygen(JNIEnv* env, jobject) {
    // Inicializar liboqs (thread-safe após primeira chamada)
    OQS_init();

    // Criar contexto de assinatura
    OQS_SIG* sig = OQS_SIG_new(OQS_SIG_alg_falcon_1024);
    if (sig == nullptr) {
        LOGE("Falha ao inicializar Falcon-1024");
        return nullptr;
    }

    // Alocar buffers para chaves
    uint8_t* public_key = static_cast<uint8_t*>(malloc(sig->length_public_key));
    uint8_t* secret_key = static_cast<uint8_t*>(malloc(sig->length_secret_key));

    if (!public_key || !secret_key) {
        LOGE("Falha ao alocar memória para chaves");
        OQS_SIG_free(sig);
        free(public_key);
        free(secret_key);
        return nullptr;
    }

    // Gerar par de chaves
    OQS_STATUS status = OQS_SIG_keypair(sig, public_key, secret_key);
    if (status != OQS_SUCCESS) {
        LOGE("Falha ao gerar par de chaves Falcon-1024");
        OQS_SIG_free(sig);
        free(public_key);
        free(secret_key);
        return nullptr;
    }

    // Criar array Java para retornar (pk + sk concatenados)
    size_t total_size = sig->length_public_key + sig->length_secret_key;
    jbyteArray result = env->NewByteArray(static_cast<jsize>(total_size));
    if (result == nullptr) {
        LOGE("Falha ao criar array Java para chaves");
        OQS_SIG_free(sig);
        free(public_key);
        free(secret_key);
        return nullptr;
    }

    // Copiar chaves para buffer temporário
    uint8_t* combined = static_cast<uint8_t*>(malloc(total_size));
    memcpy(combined, public_key, sig->length_public_key);
    memcpy(combined + sig->length_public_key, secret_key, sig->length_secret_key);

    // Copiar para array Java
    env->SetByteArrayRegion(result, 0, static_cast<jsize>(total_size),
                           reinterpret_cast<jbyte*>(combined));

    // Limpar memória sensível
    // OPENSSL_cleanse is not standard, let's zero it manually
    OPENSSL_cleanse(secret_key, sig->length_secret_key);

    // Liberar recursos
    free(combined);
    free(public_key);
    free(secret_key);
    OQS_SIG_free(sig);

    LOGI("✅ Par de chaves Falcon-1024 gerado com sucesso");
    return result;
}

// JNI: Assinar mensagem com Falcon-1024
JNIEXPORT jbyteArray JNICALL
Java_com_arkhe_core_crypto_Falcon1024_nativeSign(
    JNIEnv* env, jobject,
    jbyteArray secretKey,
    jbyteArray message) {

    OQS_init();

    // Obter ponteiros para arrays Java
    jsize sk_len = env->GetArrayLength(secretKey);
    jsize msg_len = env->GetArrayLength(message);

    jbyte* sk_bytes = env->GetByteArrayElements(secretKey, nullptr);
    jbyte* msg_bytes = env->GetByteArrayElements(message, nullptr);

    if (!sk_bytes || !msg_bytes) {
        LOGE("Falha ao acessar arrays Java");
        if (sk_bytes) env->ReleaseByteArrayElements(secretKey, sk_bytes, JNI_ABORT);
        if (msg_bytes) env->ReleaseByteArrayElements(message, msg_bytes, JNI_ABORT);
        return nullptr;
    }

    // Criar contexto de assinatura
    OQS_SIG* sig = OQS_SIG_new(OQS_SIG_alg_falcon_1024);
    if (!sig) {
        LOGE("Falha ao inicializar Falcon-1024 para assinatura");
        env->ReleaseByteArrayElements(secretKey, sk_bytes, JNI_ABORT);
        env->ReleaseByteArrayElements(message, msg_bytes, JNI_ABORT);
        return nullptr;
    }

    // Alocar buffer para assinatura
    uint8_t* signature = static_cast<uint8_t*>(malloc(sig->length_signature));
    if (!signature) {
        LOGE("Falha ao alocar memória para assinatura");
        OQS_SIG_free(sig);
        env->ReleaseByteArrayElements(secretKey, sk_bytes, JNI_ABORT);
        env->ReleaseByteArrayElements(message, msg_bytes, JNI_ABORT);
        return nullptr;
    }

    // Assinar
    size_t sig_len;
    OQS_STATUS status = OQS_SIG_sign(
        sig,
        signature,
        &sig_len,
        reinterpret_cast<uint8_t*>(msg_bytes),
        static_cast<size_t>(msg_len),
        reinterpret_cast<uint8_t*>(sk_bytes)
    );

    // Liberar recursos Java
    env->ReleaseByteArrayElements(secretKey, sk_bytes, JNI_ABORT);
    env->ReleaseByteArrayElements(message, msg_bytes, JNI_ABORT);

    if (status != OQS_SUCCESS) {
        LOGE("Falha ao assinar mensagem com Falcon-1024");
        OQS_SIG_free(sig);
        free(signature);
        return nullptr;
    }

    // Criar array Java para assinatura
    jbyteArray result = env->NewByteArray(static_cast<jsize>(sig_len));
    if (result) {
        env->SetByteArrayRegion(result, 0, static_cast<jsize>(sig_len),
                               reinterpret_cast<jbyte*>(signature));
    }

    // Limpar memória sensível
    OPENSSL_cleanse(signature, sig->length_signature);

    // Liberar recursos
    free(signature);
    OQS_SIG_free(sig);

    LOGI("✅ Mensagem assinada com Falcon-1024 (%zu bytes)", sig_len);
    return result;
}

// JNI: Verificar assinatura Falcon-1024
JNIEXPORT jboolean JNICALL
Java_com_arkhe_core_crypto_Falcon1024_nativeVerify(
    JNIEnv* env, jobject,
    jbyteArray publicKey,
    jbyteArray message,
    jbyteArray signature) {

    OQS_init();

    // Obter ponteiros para arrays Java
    jsize pk_len = env->GetArrayLength(publicKey);
    jsize msg_len = env->GetArrayLength(message);
    jsize sig_len = env->GetArrayLength(signature);

    jbyte* pk_bytes = env->GetByteArrayElements(publicKey, nullptr);
    jbyte* msg_bytes = env->GetByteArrayElements(message, nullptr);
    jbyte* sig_bytes = env->GetByteArrayElements(signature, nullptr);

    if (!pk_bytes || !msg_bytes || !sig_bytes) {
        LOGE("Falha ao acessar arrays Java para verificação");
        if (pk_bytes) env->ReleaseByteArrayElements(publicKey, pk_bytes, JNI_ABORT);
        if (msg_bytes) env->ReleaseByteArrayElements(message, msg_bytes, JNI_ABORT);
        if (sig_bytes) env->ReleaseByteArrayElements(signature, sig_bytes, JNI_ABORT);
        return JNI_FALSE;
    }

    // Criar contexto de assinatura
    OQS_SIG* sig = OQS_SIG_new(OQS_SIG_alg_falcon_1024);
    if (!sig) {
        LOGE("Falha ao inicializar Falcon-1024 para verificação");
        env->ReleaseByteArrayElements(publicKey, pk_bytes, JNI_ABORT);
        env->ReleaseByteArrayElements(message, msg_bytes, JNI_ABORT);
        env->ReleaseByteArrayElements(signature, sig_bytes, JNI_ABORT);
        return JNI_FALSE;
    }

    // Verificar assinatura
    OQS_STATUS status = OQS_SIG_verify(
        sig,
        reinterpret_cast<uint8_t*>(msg_bytes),
        static_cast<size_t>(msg_len),
        reinterpret_cast<uint8_t*>(sig_bytes),
        static_cast<size_t>(sig_len),
        reinterpret_cast<uint8_t*>(pk_bytes)
    );

    // Liberar recursos Java
    env->ReleaseByteArrayElements(publicKey, pk_bytes, JNI_ABORT);
    env->ReleaseByteArrayElements(message, msg_bytes, JNI_ABORT);
    env->ReleaseByteArrayElements(signature, sig_bytes, JNI_ABORT);

    OQS_SIG_free(sig);

    jboolean result = (status == OQS_SUCCESS) ? JNI_TRUE : JNI_FALSE;
    LOGI("✅ Verificação Falcon-1024: %s", result ? "VÁLIDA" : "INVÁLIDA");
    return result;
}

} // extern "C"