#!/bin/bash
# build_arkhe_aosp.sh
source build/envsetup.sh
lunch arkhe_arm64-userdebug

# Compilar com módulos Arkhe
make -j$(nproc) arkhe_kernel
make -j$(nproc) systemimage vendorimage

# Assinar com chave canônica
sign_target_files_apks \
    -o \
    --extra_apks ArkheRuntime.apk=PRESIGNED \
    --extra_apks ArkheSettings.apk=PRESIGNED \
    out/target/product/arkhe/obj/PACKAGING/target_files_intermediates/arkhe_arm64-target_files-eng.root.zip \
    arkhe-release-keys/
