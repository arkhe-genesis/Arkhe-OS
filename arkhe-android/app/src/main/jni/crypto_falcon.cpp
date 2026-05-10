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

    LOGI("✅ Verificação Falcon-1024: VÁLIDA (mock)");
    return JNI_TRUE;
}

} // extern "C"
