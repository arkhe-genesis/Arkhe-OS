FROM ubuntu:22.04

# Install necessary dependencies for virtualization, Android tools, and building
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    curl \
    wget \
    unzip \
    git \
    openjdk-17-jdk \
    android-sdk \
    && rm -rf /var/lib/apt/lists/*

# Set up Android SDK
ENV ANDROID_HOME=/usr/lib/android-sdk
ENV PATH=${PATH}:${ANDROID_HOME}/tools:${ANDROID_HOME}/platform-tools

# Set up workspace
WORKDIR /app

# Entrypoint for running DroidVM tasks
CMD ["./gradlew", "assembleDebug"]
