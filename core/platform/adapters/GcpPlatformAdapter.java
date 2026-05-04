package com.arkhe.os.platform.adapters;

import com.arkhe.os.platform.*;
import com.google.auth.oauth2.GoogleCredentials;
import com.google.cloud.secretmanager.v1.SecretManagerServiceClient;
import com.google.cloud.monitoring.v3.MetricServiceClient;
import com.google.cloud.container.v1.ClusterManagerClient;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class GcpPlatformAdapter implements PlatformAbstractionLayer {

    private final GcpPlatformConfig config;
    private final GoogleCredentials credentials;

    // GCP service clients (lazy initialization)
    private SecretManagerServiceClient secretManagerClient;
    private MetricServiceClient metricServiceClient;
    private ClusterManagerClient clusterManagerClient;

    public GcpPlatformAdapter(String configPath) {
        this.config = GcpPlatformConfig.load(configPath);

        // Initialize credentials: application default, service account key, or workload identity
        try {
            this.credentials = GoogleCredentials.getApplicationDefault()
                .createScoped(config.getScopes());
            log.info("GCP credentials initialized with scopes: {}", config.getScopes());
        } catch (Exception e) {
            throw new PlatformInitializationException("Failed to initialize GCP credentials", e);
        }
    }

    @Override
    public PlatformType getPlatformType() {
        return PlatformType.GCP;
    }

    @Override
    public String getRegion() {
        return config.getRegion();  // e.g., "us-central1"
    }

    @Override
    public CertificateManager getCertificateManager() {
        // GCP Certificate Manager or integration with Let's Encrypt via DNS-01
        return new GcpCertificateManager(
            config.getProjectId(),
            config.getCertificateConfig(),
            credentials
        );
    }

    @Override
    public SecretManager getSecretManager() {
        if (secretManagerClient == null) {
            secretManagerClient = SecretManagerServiceClient.create(
                SecretManagerServiceSettings.newBuilder()
                    .setCredentialsProvider(() -> credentials)
                    .build()
            );
        }
        return new GcpSecretManagerAdapter(
            secretManagerClient,
            config.getProjectId(),
            config.getSecretPrefix()
        );
    }

    @Override
    public MetricsExporter getMetricsExporter() {
        if (metricServiceClient == null) {
            metricServiceClient = MetricServiceClient.create(
                MetricServiceSettings.newBuilder()
                    .setCredentialsProvider(() -> credentials)
                    .build()
            );
        }
        return new GcpCloudMonitoringExporter(
            metricServiceClient,
            config.getProjectId(),
            config.getMetricsPrefix()
        );
    }

    @Override
    public ComputeOrchestrator getComputeOrchestrator() {
        if (clusterManagerClient == null) {
            clusterManagerClient = ClusterManagerClient.create(
                ClusterManagerSettings.newBuilder()
                    .setCredentialsProvider(() -> credentials)
                    .build()
            );
        }
        return new GcpGkeOrchestrator(
            clusterManagerClient,
            config.getProjectId(),
            config.getLocation(),  // region or zone
            config.getGkeClusterName()
        );
    }

    // ... other PAL methods implemented similarly
}