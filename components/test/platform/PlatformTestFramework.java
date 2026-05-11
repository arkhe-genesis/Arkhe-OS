package com.arkhe.os.test.platform;

import com.arkhe.os.platform.PlatformAbstractionLayer;
import com.arkhe.os.platform.PlatformFactory;
import com.arkhe.os.platform.PlatformType;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;

/**
 * Base test class for cross-platform ARKHE OS tests.
 *
 * Usage:
 * @ExtendWith(PlatformTestExtension.class)
 * class MyCrossPlatformTest extends PlatformTestFramework {
 *   @ParameterizedTest
 *   @EnumSource(PlatformType.class)
 *   void testCertificateRotation(PlatformType platform) {
 *     PlatformAbstractionLayer pal = createPlatform(platform);
 *     // Test logic using PAL interface
 *   }
 * }
 */
@Slf4j
@ExtendWith(PlatformTestExtension.class)
public abstract class PlatformTestFramework {

    /**
     * Creates a PlatformAbstractionLayer for the specified platform.
     * Uses test configuration from test/resources/platforms/{platform}/test-config.yaml
     */
    protected PlatformAbstractionLayer createPlatform(PlatformType platform) {
        String configPath = String.format("test/resources/platforms/%s/test-config.yaml",
            platform.getCode());
        log.info("Creating platform adapter for tests: {} (config: {})",
            platform, configPath);
        return PlatformFactory.create(platform, configPath);
    }

    /**
     * Skips test if platform is not available in current environment.
     * Useful for local development where not all platforms are accessible.
     */
    protected void assumePlatformAvailable(PlatformType platform) {
        boolean available = switch (platform) {
            case AZURE -> System.getenv("AZURE_SUBSCRIPTION_ID") != null;
            case GCP -> System.getenv("GCP_PROJECT_ID") != null;
            case APPLE -> System.getProperty("os.name").toLowerCase().contains("mac");
            case ORACLE -> System.getenv("OCI_TENANCY_OCID") != null;
            case KUBERNETES -> true;  // Always available via kind/minikube
        };
        org.junit.jupiter.api.Assumptions.assumeTrue(available,
            "Platform " + platform + " not available in test environment");
    }

    /**
     * Common test assertions for certificate management across platforms.
     */
    protected void assertCertificateManagerBehavior(CertificateManager cm) {
        // Test certificate issuance
        var cert = cm.issueCertificate("test.example.com", 30);
        assertNotNull(cert);
        assertNotNull(cert.getPrivateKey());
        assertNotNull(cert.getCertificateChain());

        // Test certificate rotation
        var rotated = cm.rotateCertificate(cert, 30);
        assertNotNull(rotated);
        assertNotEquals(cert.getSerialNumber(), rotated.getSerialNumber());

        // Test certificate revocation
        cm.revokeCertificate(rotated);
        // Verify revocation status (platform-specific implementation)
    }

    /**
     * Common test assertions for secret management across platforms.
     */
    protected void assertSecretManagerBehavior(SecretManager sm) {
        // Test secret creation
        String secretName = "test-secret-" + System.currentTimeMillis();
        sm.createSecret(secretName, "test-value".getBytes());

        // Test secret retrieval
        byte[] retrieved = sm.getSecret(secretName);
        assertArrayEquals("test-value".getBytes(), retrieved);

        // Test secret rotation
        sm.rotateSecret(secretName, "new-value".getBytes());
        byte[] rotated = sm.getSecret(secretName);
        assertArrayEquals("new-value".getBytes(), rotated);

        // Test secret deletion
        sm.deleteSecret(secretName);
        assertNull(sm.getSecret(secretName));
    }
}