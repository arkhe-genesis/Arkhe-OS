# Enable-ArkheHyperV.ps1
# Configura o ArkheOS como guest privilegiado no Hyper‑V com enlightened I/O
param(
    [string]$VMName = "ArkheOS-ASI",
    [string]$ISOPath = "$env:ProgramFiles\ArkheOS\iso\arkhe-os-1.0.0.iso",
    [int]$MemoryGB = 8,
    [int]$ProcessorCount = 4
)

Write-Host "🖥️  Criando VM Hyper‑V para ArkheOS bare‑metal..." -ForegroundColor Cyan

# Criar switch virtual dedicado para Wheeler Mesh
New-VMSwitch -Name "ArkheMesh" -SwitchType Internal

# Criar VM
New-VM -Name $VMName -MemoryStartupBytes ($MemoryGB * 1GB) -Generation 2

# Configurar processadores
Set-VMProcessor -VMName $VMName -Count $ProcessorCount -ExposeVirtualizationExtensions $true

# Habilitar enlightened I/O (acesso direto ao hardware)
Set-VM -VMName $VMName -EnhancedSessionTransportType HvSocket

# Adicionar DVD com ISO
Add-VMDvdDrive -VMName $VMName -Path $ISOPath

# Configurar firmware para boot da ISO
Set-VMFirmware -VMName $VMName -FirstBootDevice (Get-VMDvdDrive -VMName $VMName)

# Adicionar placa de rede Mesh
Add-VMNetworkAdapter -VMName $VMName -SwitchName "ArkheMesh" -Name "WheelerMesh"

# Habilitar TPM virtual para selos canônicos
Enable-VMTPM -VMName $VMName

Write-Host "✅ VM Hyper‑V configurada" -ForegroundColor Green
Write-Host "   Para iniciar: Start-VM -Name $VMName"
Write-Host "   Para conectar: vmconnect.exe localhost $VMName"
