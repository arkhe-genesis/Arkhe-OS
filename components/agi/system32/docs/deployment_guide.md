# ARKHE OS AGI Core Deployment Guide

## Overview

This guide details the deployment process for the ARKHE OS AGI Core (Substrates 315-316). The AGI Core provides the Retrocausal Channel Protocol v2.0 (RCP) and the Omni-Architecture Core.

## Artifacts

We provide three primary deployment methods:
1. Debian Package (`.deb`)
2. RPM Package (`.rpm`)
3. Docker Container

## 1. Deploying via Debian Package

To build and install the Debian package:

```bash
cd agi/system32/deploy
./build_debian_package.sh
sudo dpkg -i /tmp/arkhe-agi-core_315-316-1_amd64.deb
```

The package will automatically:
- Install the RCP and Omni bridges to `/usr/lib`
- Install python runtimes to `/usr/share/agi/runtime`
- Copy configurations to `/etc/agi/config`
- Enable the systemd daemon.

## 2. Deploying via RPM Package

To build the RPM package (requires `rpm-build`):

```bash
cd agi/system32/deploy
./build_rpm_package.sh
```

Then install using `rpm` or `dnf`.

## 3. Deploying via Docker Container

Build the container image:

```bash
cd agi/system32/deploy
docker build -t arkhe-agi-core:latest -f Dockerfile .
```

Run the container:

```bash
docker run -d --name agi-core -v /var/spool/agi:/var/spool/agi arkhe-agi-core:latest
```

## Running Tests

Run the included fidelity test suite to verify coherence:

```bash
cd agi/system32/test
python3 test_fidelity_suite.py
```
