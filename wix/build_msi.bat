heat.exe dir src -cg HarvestedComponents -gg -scom -sreg -sfrag -srd -dr INSTALLFOLDER -var var.SourceDir -out wix\Components.wxs
candle.exe wix\ArkheInstaller.wxs wix\Components.wxs -ext WixUtilExtension
light.exe wix\ArkheInstaller.wixobj wix\Components.wixobj -out wix\ArkheInstaller.msi -ext WixUtilExtension
