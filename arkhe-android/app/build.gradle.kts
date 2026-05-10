// app/build.gradle.kts
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp") version "1.9.20-1.0.14" // Para bindings Kotlin/Native
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.arkhe.cathedral"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.arkhe.cathedral"
        minSdk = 28  // Android 9.0+ para StrongBox support
        minSdk = 28
        targetSdk = 34
        versionCode = 1
        versionName = "4.3.5"

        // Configuração NDK para código nativo (Falcon-1024, BN254 pairing)
        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
            cppFlags += listOf(
                "-std=c++17",
                "-O3",
                "-fvisibility=hidden"
            )
        }

        // Configuração para código nativo
        externalNativeBuild {
            cmake {
                cppFlags += "-std=c++17 -O3"
                arguments += listOf(
                    "-DANDROID_STL=c++_static",
                    "-DENABLE_FALCON=ON",
                    "-DENABLE_BN254=ON"
                )
            }
        }

        // Build config fields para segurança
        buildConfigField("String", "NATIVE_CODE_HASH", "\"${computeNativeHash()}\"")
        buildConfigField("String", "GENESIS_HASH", "\"a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4\"")
        buildConfigField("Boolean", "TEE_ENABLED", "true")
    }

    // Assinatura do APK (em produção: usar keystore seguro)
    signingConfigs {
        create("release") {
            storeFile = file("../keystore/arkhe-release.jks")
            storePassword = System.getenv("ARKHE_KEYSTORE_PASSWORD")
            keyAlias = System.getenv("ARKHE_KEY_ALIAS")
            keyPassword = System.getenv("ARKHE_KEY_PASSWORD")
            enableV2Signing = true
            enableV3Signing = true
            enableV4Signing = true  // APK Signature Scheme v4 para Android 11+
        }
        externalNativeBuild {
            cmake {
                cppFlags += "-std=c++17 -O3"
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("release")
        }
        debug {
            applicationIdSuffix = ".debug"
            isDebuggable = true
        }
    }

    // Kotlin options
    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf(
            "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
            "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api"
        )
    }

    // Compose
    buildFeatures {
        compose = true
        buildConfig = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.4"
    }

    // Native build
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/jni/CMakeLists.txt")
            version = "3.22.1"
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    testImplementation("junit:junit:4.13.2")
}
