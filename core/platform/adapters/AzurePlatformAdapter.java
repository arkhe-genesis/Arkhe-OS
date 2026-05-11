package com.arkhe.os.platform.adapters;

import com.arkhe.os.platform.*;
import com.arkhe.os.security.CertificateManager;
import com.arkhe.os.security.SecretManager;
import com.arkhe.os.monitoring.MetricsExporter;
import com.arkhe.os.compute.ComputeOrchestrator;
import com.arkhe.os.network.NetworkProvider;
import com.azure.core.credential.TokenCredential;
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.resourcemanager.AzureResourceManager;
import com.azure.resourcemanager.resources.fluentcore.arm.Region;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class AzurePlatformAdapter implements PlatformAbstractionLayer {

    private final AzurePlatformConfig config;
    private final TokenCredential credential;
    private final AzureResourceManager azure;

    // Platform-specific components (lazy initialization)
    private CertificateManager certificateManager;
    private SecretManager secretManager;
    private MetricsExporter metricsExporter;
    private ComputeOrchestrator computeOrchestrator;
    private NetworkProvider networkProvider;

    public AzurePlatformAdapter(String configPath) {
        this.config = AzurePlatformConfig.load(configPath);
        this.credential = new DefaultAzureCredentialBuilder()
            .tenantId(config.getTenantId())
            .build();
        this.azure = AzureResourceManager
            .authenticate(credential, config.getSubscriptionId())
            .withRegion(Region.fromName(config.getRegion()));

        log.info("Azure Platform Adapter initialized: subscription={}, region={}",
            config.getSubscriptionId(), config.getRegion());
    }

    @Override
    public PlatformType getPlatformType() {
        return PlatformType.AZURE;
    }

    @Override
    public String getRegion() {
        return config.getRegion();
    }

    @Override
    public CertificateManager getCertificateManager() {
        if (certificateManager == null) {
            certificateManager = new AzureCertificateManager(
                azure,
                config.getKeyVaultName(),
                config.getCertificatePolicy()
            );
        }
        return certificateManager;
    }

    @Override
    public SecretManager getSecretManager() {
        if (secretManager == null) {
            secretManager = new AzureKeyVaultSecretManager(
                azure,
                config.getKeyVaultName(),
                config.getSecretPrefix()
            );
        }
        return secretManager;
    }

    @Override
    public MetricsExporter getMetricsExporter() {
        if (metricsExporter == null) {
            metricsExporter = new AzureMonitorMetricsExporter(
                config.getWorkspaceId(),
                config.getMetricsNamespace(),
                credential
            );
        }
        return metricsExporter;
    }

    @Override
    public ComputeOrchestrator getComputeOrchestrator() {
        if (computeOrchestrator == null) {
            computeOrchestrator = new AzureAksOrchestrator(
                azure,
                config.getAksClusterName(),
                config.getResourceGroupName()
            );
        }
        return computeOrchestrator;
    }

    @Override
    public NetworkProvider getNetworkProvider() {
        if (networkProvider == null) {
            networkProvider = new AzureNetworkProvider(
                azure,
                config.getVnetName(),
                config.getSubnetName()
            );
        }
        return networkProvider;
    }

    @Override
    @SuppressWarnings("unchecked")
    public <T> T getPlatformConfig(Class<T> configType) {
        if (configType.isInstance(config)) {
            return (T) config;
        }
        throw new IllegalArgumentException(
            "Config type not supported: " + configType.getName());
    }

    @Override
    public void validatePlatformRequirements() throws PlatformValidationError {
        // Validate Azure-specific requirements
        if (!azure.subscriptions().getById(config.getSubscriptionId()).enabled()) {
            throw new PlatformValidationError("Subscription not enabled: " + config.getSubscriptionId());
        }

        // Validate Key Vault access
        try {
            azure.vaults().getByResourceGroup(
                config.getResourceGroupName(),
                config.getKeyVaultName()
            );
        } catch (Exception e) {
            throw new PlatformValidationError(
                "Cannot access Key Vault: " + config.getKeyVaultName(), e);
        }

        // Validate AKS cluster exists and is running
        var cluster = azure.kubernetesClusters()
            .getByResourceGroup(config.getResourceGroupName(), config.getAksClusterName());
        if (cluster == null || cluster.provisioningState() != "Succeeded") {
            throw new PlatformValidationError("AKS cluster not ready: " + config.getAksClusterName());
        }

        log.info("Azure platform requirements validated successfully");
    }

    @Override
    public void initializePlatform() throws PlatformInitializationException {
        try {
            // Register ARKHE resource providers if not already registered
            azure.providers().register("Microsoft.ContainerService");
            azure.providers().register("Microsoft.KeyVault");
            azure.providers().register("Microsoft.Monitor");

            // Configure Azure AD app registration for ARKHE service principal
            if (config.isAutoConfigureAad()) {
                configureAzureAdIntegration();
            }

            // Set up diagnostic settings for ARKHE resources
            configureDiagnostics();

            log.info("Azure platform initialization completed");
        } catch (Exception e) {
            throw new PlatformInitializationException("Failed to initialize Azure platform", e);
        }
    }

    @Override
    public void shutdownPlatform() {
        // Clean up temporary resources if configured
        if (config.isCleanupOnShutdown()) {
            log.info("Cleaning up temporary Azure resources...");
            // Implementation depends on resource tagging strategy
        }

        // Close Azure SDK clients
        if (azure != null) {
            // Azure ResourceManager doesn't have explicit close; rely on GC
        }

        log.info("Azure platform shutdown completed");
    }

    // Azure-specific helper methods
    private void configureAzureAdIntegration() {
        // Implementation: Create/update Azure AD app registration,
        // assign RBAC roles, configure federated credentials for workload identity
        log.debug("Configuring Azure AD integration for ARKHE workloads");
    }

    private void configureDiagnostics() {
        // Implementation: Enable diagnostic settings for AKS, Key Vault, etc.
        // to stream logs to Log Analytics workspace
        log.debug("Configuring Azure diagnostic settings");
    }
}
