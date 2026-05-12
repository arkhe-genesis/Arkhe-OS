@echo off
echo Building ARKHE OS MSI with WiX Toolset...
candle ARKHE.wxs -ext WixUtilExtension -out ARKHE.wixobj
light ARKHE.wixobj -ext WixUtilExtension -out ARKHE.msi
echo Build complete.