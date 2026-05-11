#include <jni.h>
#include <android/log.h>
// #include <oqs/oqs.h>
#include <cstring>
#include <cstdlib>

#define TAG "ArkheNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

extern "C" {

// JNI: Gerar par de chaves Falcon-1024
JNIEXPORT jbyteArray JNICALL
Java_com_arkhe_core_crypto_Falcon1024_nativeKeygen(JNIEnv* env, jobject) {
    LOGI("✅ Par de chaves Falcon-1024 gerado com sucesso (mock)");
    return env->NewByteArray(10);
}

// JNI: Assinar mensagem com Falcon-1024
JNIEXPORT jbyteArray JNICALL
Java_com_arkhe_core_crypto_Falcon1024_nativeSign(
    JNIEnv* env, jobject,
    jbyteArray secretKey,
    jbyteArray message) {

    LOGI("✅ Mensagem assinada com Falcon-1024 (mock)");
    return env->NewByteArray(10);
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
    LOGI("✅ Verificação Falcon-1024: VÁLIDA (mock)");
    return JNI_TRUE;
}

} // extern "C"
