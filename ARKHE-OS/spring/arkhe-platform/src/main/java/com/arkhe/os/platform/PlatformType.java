package com.arkhe.os.platform;

public enum PlatformType {
    AZURE("Microsoft Azure", "azure"),
    GCP("Google Cloud Platform", "gcp"),
    APPLE("Apple Platform", "apple"),
    ORACLE("Oracle Cloud Infrastructure", "oracle"),
    GENERIC_KUBERNETES("Generic Kubernetes", "generic-k8s"),
    UNKNOWN("Unknown Platform", "unknown");

    private final String displayName;
    private final String configPrefix;

    PlatformType(String displayName, String configPrefix) {
        this.displayName = displayName;
        this.configPrefix = configPrefix;
    }

    public String getDisplayName() { return displayName; }
    public String getConfigPrefix() { return configPrefix; }
}
