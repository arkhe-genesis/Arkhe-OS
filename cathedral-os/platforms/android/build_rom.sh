#!/bin/bash
# Uso: ./build_rom.sh /caminho/para/aosp/root
AOSP_ROOT=$1
OVERLAY_DIR="$(pwd)/aosp_overlay"

echo "[Cathedral OS] Injetando AIDL no Framework..."
cp $OVERLAY_DIR/frameworks/base/core/java/android/os/ICathedralAgent.aidl \
   $AOSP_ROOT/frameworks/base/core/java/android/os/

echo "[Cathedral OS] Injetando Políticas SELinux..."
cat $OVERLAY_DIR/system/sepolicy/private/cathedral.te >> \
   $AOSP_ROOT/system/sepolicy/private/private_sepolicy.cil

echo "[Cathedral OS] Iniciando build do AOSP (isso levará horas)..."
cd $AOSP_ROOT
source build/envsetup.sh
lunch aosp_arm64-userdebug
make -j$(nproc)
