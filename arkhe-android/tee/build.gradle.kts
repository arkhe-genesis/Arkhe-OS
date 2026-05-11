plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.arkhe.tee"
    compileSdk = 34

    defaultConfig {
        minSdk = 28
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}
