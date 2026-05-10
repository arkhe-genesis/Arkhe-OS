#include <jni.h>
#include <android/log.h>

#define TAG "ArkheCore"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)

extern "C" {
    JNIEXPORT void JNICALL
    Java_com_arkhe_core_ArkheNative_init(JNIEnv* env, jobject) {
        LOGI("Arkhe Core initialized.");
    }
}
