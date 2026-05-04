package com.arkhe.os.platform;

import com.arkhe.os.security.CertificateManager;
import com.arkhe.os.security.SecretManager;
import com.arkhe.os.monitoring.MetricsExporter;
import com.arkhe.os.compute.ComputeOrchestrator;
import com.arkhe.os.network.NetworkProvider;

/**
 * Platform Abstraction Layer (PAL) — Interface for multi-platform ARKHE OS deployment.
 *
 * All platform-specific implementations must implement this interface to ensure
 * consistent behavior across Microsoft, Google, Apple, and Oracle ecosystems.
 */
public interface PlatformAbstractionLayer {

    /**
     * Returns the platform identifier (azure, gcp, apple, oracle).
     */
    PlatformType getPlatformType();

    /**
     * Returns the region/zone where the ARKHE instance is deployed.
     */
    String getRegion();

    /**
     * Certificate management abstraction.
     * Handles TLS/mTLS certificate issuance, rotation, and revocation.
     */
    CertificateManager getCertificateManager();

    /**
     * Secret management abstraction.
     * Handles secure storage and retrieval of sensitive configuration.
     */
    SecretManager getSecretManager();

    /**
     * Metrics and observability abstraction.
     * Exports ARKHE metrics to platform-native monitoring systems.
     */
    MetricsExporter getMetricsExporter();

    /**
     * Compute orchestration abstraction.
     * Manages deployment, scaling, and lifecycle of ARKHE workloads.
     */
    ComputeOrchestrator getComputeOrchestrator();

    /**
     * Network provider abstraction.
     * Configures VPC/VNet, load balancing, and service mesh integration.
     */
    NetworkProvider getNetworkProvider();

    /**
     * Returns platform-specific configuration as typed object.
     * @param <T> The platform-specific config type
     * @return Typed configuration object
     */
    <T> T getPlatformConfig(Class<T> configType);

    /**
     * Validates that the current platform meets ARKHE OS requirements.
     * @throws PlatformValidationError if requirements not met
     */
    void validatePlatformRequirements() throws PlatformValidationError;

    /**
     * Performs platform-specific initialization before ARKHE core startup.
     */
    void initializePlatform() throws PlatformInitializationException;

    /**
     * Performs platform-specific cleanup during ARKHE OS shutdown.
     */
    void shutdownPlatform();
}
