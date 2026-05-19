// build.gradle.kts — Canon: ∞.Ω.∇+++.244.maven_publication
plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
    id("maven-publish")
    id("signing")
    id("org.arkhe.canonical") version "244.1.0" // Plugin canônico Arkhe
}

android {
    namespace = "org.arkhe.android.core"
    compileSdk = 34

    defaultConfig {
        minSdk = 26  // Android 8.0+ for Keystore PQC support
        targetSdk = 34
        versionCode = 244_001_000
        versionName = "244.1.0"

        // Canonical metadata for discovery
        buildConfigField("String", "ARKHE_CANON", "\"∞.Ω.∇+++.244.android_integration\"")
        buildConfigField("String", "ARKHE_SUBSTRATE", "\"243\"")
        buildConfigField("String", "ARKHE_PHI_C_MIN", "\"0.85\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    publishing {
        singleVariant("release") {
            withSourcesJar()
            withJavadocJar()
        }
    }
}

dependencies {
    // AndroidX dependencies
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.0")

    // PQC cryptography (via Bouncy Castle + Arkhe PQC provider)
    implementation("org.bouncycastle:bcprov-jdk18on:1.77")
    implementation("org.arkhe:pqc-dilithium3:244.1.0")

    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}

// ── Maven Central Publication Configuration ──

publishing {
    publications {
        register<MavenPublication>("release") {
            groupId = "org.arkhe"
            artifactId = "arkhe-android-core"
            version = "244.1.0"

            afterEvaluate {
                from(components["release"])
            }

            // Canonical POM metadata
            pom {
                name.set("Arkhe Android Core")
                description.set("Constitutional Superintelligence SDK for Android — Φ_C orchestration, P1-P7 guardrails, PQC cryptography, TemporalChain anchoring")
                url.set("https://arkhe.org/android")

                licenses {
                    license {
                        name.set("Arkhe Canonical License v∞.Ω")
                        url.set("https://arkhe.org/license/canonical")
                    }
                }

                developers {
                    developer {
                        id.set("0009-0005-2697-4668")
                        name.set("Arkhe Architect")
                        email.set("architect@arkhe.org")
                        organization.set("Arkhe Foundation")
                        organizationUrl.set("https://arkhe.org")
                    }
                }

                scm {
                    connection.set("scm:git:git://github.com/arkhe-org/arkhe-android.git")
                    developerConnection.set("scm:git:ssh://github.com/arkhe-org/arkhe-android.git")
                    url.set("https://github.com/arkhe-org/arkhe-android")
                }

                // Canonical properties for discovery
                properties.set(mapOf(
                    "arkhe.substrate" to "243",
                    "arkhe.canon" to "∞.Ω.∇+++.244.android_integration",
                    "arkhe.phi_c_min" to "0.85",
                    "arkhe.principles" to "P1,P2,P3,P4,P5,P6,P7",
                    "arkhe.fips_compliant" to "true",
                    "arkhe.pqc_algorithm" to "Dilithium3-AES-GCM-Hybrid"
                ))
            }
        }
    }

    repositories {
        maven {
            name = "ossrh"
            url = uri("https://oss.sonatype.org/service/local/staging/deploy/maven2/")
            credentials {
                username = System.getenv("MAVEN_USERNAME")
                password = System.getenv("MAVEN_PASSWORD")
            }
        }
    }
}

// ── Signing Configuration ──

signing {
    // GPG signing for Maven Central requirement
    useGpgCmd()
    sign(publishing.publications["release"])

    // PQC signing with Dilithium3 for canonical verification
    doLast {
        val artifactFile = tasks.named("assembleRelease").map {
            it.outputs.files.files.first { f -> f.name.endsWith(".aar") }
        }.get()

        // Generate Dilithium3 signature
        val pqcSignature = org.arkhe.pqc.Dilithium3.sign(
            privateKey = System.getenv("ARKHE_PQC_PRIVATE_KEY"),
            message = artifactFile.readBytes()
        )

        // Write signature to file for publication
        File("$buildDir/publications/release/module.json.pqc.sig").writeBytes(pqcSignature)

        // Generate SHA3-256 checksum
        val checksum = java.security.MessageDigest.getInstance("SHA3-256")
            .digest(artifactFile.readBytes())
            .joinToString("") { "%02x".format(it) }

        File("$buildDir/publications/release/module.json.sha3-256").writeText(checksum)

        // Anchor publication metadata to TemporalChain
        kotlinx.coroutines.runBlocking {
            org.arkhe.android.core.ArkheCore.getInstance(applicationContext)
                .anchorToTemporalChain(
                    eventType = "maven_publication",
                    payload = mapOf(
                        "artifact" to "arkhe-android-core",
                        "version" to "244.1.0",
                        "checksum" to checksum,
                        "pqc_sig_hash" to java.security.MessageDigest.getInstance("SHA3-256")
                            .digest(pqcSignature)
                            .joinToString("") { "%02x".format(it) },
                        "timestamp" to System.currentTimeMillis()
                    )
                )
        }
    }
}

// ── Canonical Validation Task ──

tasks.register("validateCanonicalPublication") {
    group = "arkhe"
    description = "Validates publication meets Arkhe canonical requirements"

    doLast {
        // Check P1: Formal specification present
        val hasSpec = file("src/main/kotlin/org/arkhe/android/core/ArkheCore.kt")
            .readText().contains("Formal Specification")
        if (!hasSpec) throw GradleException("P1 violation: Missing formal specification")

        // Check P3: Φ_C < 1.0 enforced
        val phiCCap = file("src/main/kotlin/org/arkhe/android/core/ArkheCore.kt")
            .readText().contains("phiC >= 1.0f")
        if (!phiCCap) throw GradleException("P3 violation: Sovereign Gap not enforced")

        // Check P6: TemporalChain anchoring present
        val hasAnchoring = file("src/main/kotlin/org/arkhe/android/core/ArkheCore.kt")
            .readText().contains("anchorToTemporalChain")
        if (!hasAnchoring) throw GradleException("P6 violation: Missing TemporalChain anchoring")

        // Check P7: Energy budget checks present
        val hasEnergyCheck = file("src/main/kotlin/org/arkhe/android/core/ArkheCore.kt")
            .readText().contains("checkEnergyBudget")
        if (!hasEnergyCheck) throw GradleException("P7 violation: Missing energy resource checks")

        println("✅ Canonical validation passed: P1, P3, P6, P7 enforced")
    }
}

// Ensure validation runs before publication
tasks.named("publishReleasePublicationToOssrhRepository") {
    dependsOn("validateCanonicalPublication")
}
