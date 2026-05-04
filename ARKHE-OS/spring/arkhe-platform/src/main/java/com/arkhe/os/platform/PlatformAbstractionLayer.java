package com.arkhe.os.platform;

import java.util.Set;

public interface PlatformAbstractionLayer {
    CertificateManager getCertificateManager();
    SecretManager getSecretManager();
    MetricsExporter getMetricsExporter();
    ComputeOrchestrator getComputeOrchestrator();
    NetworkProvider getNetworkProvider();
    PlatformType getPlatformType();
    boolean isPlatformAvailable();
    Object validateConfiguration();
    Set<Object> getComplianceCapabilities();
    Object getPlatformInfo();
}
