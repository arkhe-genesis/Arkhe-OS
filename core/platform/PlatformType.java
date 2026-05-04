package com.arkhe.os.platform;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum PlatformType {
    AZURE("azure", "Microsoft Azure", "https://azure.microsoft.com"),
    GCP("gcp", "Google Cloud Platform", "https://cloud.google.com"),
    APPLE("apple", "Apple Platform", "https://developer.apple.com"),
    ORACLE("oracle", "Oracle Cloud Infrastructure", "https://oracle.com/cloud"),
    KUBERNETES("kubernetes", "Generic Kubernetes", "https://kubernetes.io");

    private final String code;
    private final String displayName;
    private final String documentationUrl;

    public static PlatformType fromCode(String code) {
        for (PlatformType type : values()) {
            if (type.code.equalsIgnoreCase(code)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown platform type: " + code);
    }
}
