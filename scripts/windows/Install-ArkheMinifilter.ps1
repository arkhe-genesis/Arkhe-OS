# Install-ArkheMinifilter.ps1
$driverPath = "$env:ProgramFiles\ArkheOS\drivers\ArkheFsMiniFilter.sys"
$serviceName = "ArkheFsMiniFilter"

# Copiar driver
Copy-Item .\ArkheFsMiniFilter.sys $driverPath -Force

# Criar serviço do driver
sc.exe create $serviceName type=filesys start=auto binPath=$driverPath

# Iniciar
sc.exe start $serviceName

Write-Host "✅ Arkhe FS Minifilter instalado e ativo" -ForegroundColor Green
Write-Host "   Todos os arquivos NTFS agora são automaticamente selados."
