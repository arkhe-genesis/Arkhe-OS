// app/build.gradle.kts
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp") version "1.9.20-1.0.14" // Para bindings Kotlin/Native
}

android {
    namespace = "com.arkhe.cathedral"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.arkhe.cathedral"
        minSdk = 28  // Android 9.0+ para StrongBox support
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
    externalNativeBuild {
        cmake {
            path = file("src/main/jni/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    // Packaging options
    packaging {
        resources {
            excludes += listOf(
                "META-INF/DEPENDENCIES",
                "META-INF/LICENSE",
                "META-INF/LICENSE.txt",
                "META-INF/NOTICE",
                "META-INF/NOTICE.txt"
            )
        }
        jniLibs {
            useLegacyPackaging = false
        }
    }
}

dependencies {
    // ARKHE Core (módulo local ou Maven)
    implementation(project(":core"))
    implementation(project(":tee"))  // Opcional: via Play Feature Delivery

    // AndroidX
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")

    // Jetpack Compose
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    // Crypto (para fallback quando TEE não disponível)
    implementation("org.bouncycastle:bcprov-jdk18on:1.77")

    // Networking
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")

    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

// Função auxiliar para hash do código nativo
fun computeNativeHash(): String {
    // Em produção: calcular SHA3-256 do .so compilado
    // Aqui: placeholder
    return "placeholder_native_hash_32chars"
}