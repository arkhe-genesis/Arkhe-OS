package com.arkhe.os.platform;

import com.arkhe.os.platform.adapters.*;
import lombok.experimental.UtilityClass;
import lombok.extern.slf4j.Slf4j;

@UtilityClass
@Slf4j
public class PlatformFactory {

    /**
     * Creates a PlatformAbstractionLayer instance for the specified platform.
     *
     * @param platformType The target platform
     * @param configPath Path to platform-specific configuration file
     * @return Initialized PAL implementation
     */
    public static PlatformAbstractionLayer create(
            PlatformType platformType,
            String configPath) {

        log.info("Creating PlatformAbstractionLayer for: {}", platformType.getDisplayName());

        return switch (platformType) {
            case AZURE -> new AzurePlatformAdapter(configPath);
            case GCP -> new GcpPlatformAdapter(configPath);
            case APPLE -> new ApplePlatformAdapter(configPath);
            case ORACLE -> new OraclePlatformAdapter(configPath);
            case KUBERNETES -> new KubernetesPlatformAdapter(configPath);
            default -> throw new IllegalArgumentException(
                "Platform not supported: " + platformType);
        };
    }

    /**
     * Auto-detects the current platform and creates appropriate adapter.
     * Detection order: environment variables → metadata service → fallback to Kubernetes.
     */
    public static PlatformAbstractionLayer autoDetect(String configPath) {
        PlatformType detected = detectPlatform();
        log.info("Auto-detected platform: {}", detected.getDisplayName());
        return create(detected, configPath);
    }

    private static PlatformType detectPlatform() {
        // Check environment variables first (explicit override)
        String platformEnv = System.getenv("ARKHE_PLATFORM");
        if (platformEnv != null && !platformEnv.isBlank()) {
            return PlatformType.fromCode(platformEnv);
        }

        // Check Azure metadata service
        if (isAzureEnvironment()) {
            return PlatformType.AZURE;
        }

        // Check GCP metadata service
        if (isGcpEnvironment()) {
            return PlatformType.GCP;
        }

        // Check Apple platform indicators
        if (isAppleEnvironment()) {
            return PlatformType.APPLE;
        }

        // Check Oracle Cloud indicators
        if (isOracleEnvironment()) {
            return PlatformType.ORACLE;
        }

        // Default to generic Kubernetes
        log.warn("Could not auto-detect platform; defaulting to Kubernetes");
        return PlatformType.KUBERNETES;
    }

    // Platform detection helpers (simplified for brevity)
    private static boolean isAzureEnvironment() {
        try {
            // Azure IMDS endpoint
            var request = java.net.http.HttpRequest.newBuilder()
                .uri(java.net.URI.create("http://169.254.169.254/metadata/instance?api-version=2021-02-01"))
                .header("Metadata", "true")
                .timeout(java.time.Duration.ofSeconds(2))
                .build();
            var client = java.net.http.HttpClient.newBuilder()
                .connectTimeout(java.time.Duration.ofSeconds(2))
                .build();
            var response = client.send(request,
                java.net.http.HttpResponse.BodyHandlers.discarding());
            return response.statusCode() == 200;
        } catch (Exception e) {
            return false;
        }
    }

    private static boolean isGcpEnvironment() {
        try {
            // GCP metadata server
            var request = java.net.http.HttpRequest.newBuilder()
                .uri(java.net.URI.create("http://metadata.google.internal/computeMetadata/v1/instance"))
                .header("Metadata-Flavor", "Google")
                .timeout(java.time.Duration.ofSeconds(2))
                .build();
            var client = java.net.http.HttpClient.newBuilder()
                .connectTimeout(java.time.Duration.ofSeconds(2))
                .build();
            var response = client.send(request,
                java.net.http.HttpResponse.BodyHandlers.discarding());
            return response.statusCode() == 200;
        } catch (Exception e) {
            return false;
        }
    }

    private static boolean isAppleEnvironment() {
        // Check for Apple-specific system properties or files
        return System.getProperty("os.name").toLowerCase().contains("mac") ||
               java.nio.file.Files.exists(java.nio.file.Path.of("/System/Library/CoreServices"));
    }

    private static boolean isOracleEnvironment() {
        // Check for OCI-specific environment or metadata
        return System.getenv("OCI_REGION") != null ||
               System.getenv("OCI_CLI_PROFILE") != null ||
               java.nio.file.Files.exists(java.net.URI.create("http://169.254.169.254/opc/v1/instance"));
    }
}
