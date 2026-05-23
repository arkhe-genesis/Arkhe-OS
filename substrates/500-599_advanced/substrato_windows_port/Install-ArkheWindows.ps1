#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [ValidateSet("WSL2","Native","Container")]
    [string]$Mode = "WSL2"
)

Write-Host "ARKHE OS v∞.Ω.∇+++ — Instalador Windows [$Mode]" -ForegroundColor Cyan

# 1. Pré-requisitos modo WSL2
if ($Mode -eq "WSL2") {
    wsl --install --no-distribution
    winget install Docker.DockerDesktop
}

# 2. Estrutura canônica
$Dirs = @("C:\Arkhe\Substratos","C:\Arkhe\Verificadores","C:\Arkhe\Proofs","C:\Arkhe\Logs","C:\Arkhe\Config","C:\Arkhe\Skills")
$Dirs | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force | Out-Null }

# 3. Python + venv
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    winget install Python.Python.3.12
}
python -m venv C:\Arkhe\venv
& C:\Arkhe\venv\Scripts\python.exe -m pip install --upgrade pip
& C:\Arkhe\venv\Scripts\pip.exe install sympy numpy scipy matplotlib cryptography pytest flask fastapi uvicorn pyyaml pywin32

# 4. Copiar código (assumir repo em C:\Arkhe-Source)
Copy-Item -Path "C:\Arkhe-Source\arkhe\*" -Destination "C:\Arkhe\" -Recurse -Force

# 5. Gerar manifesto SHA3-256
& C:\Arkhe\venv\Scripts\python.exe -c "
import hashlib, pathlib
base = pathlib.Path('C:/Arkhe')
files = list((base/'Substratos').rglob('*.py')) + [base/'arkhe_cli.py', base/'verify_constitution_windows.py']
with open(base/'Proofs'/'manifest.sha3', 'w') as mf:
    for f in files:
        h = hashlib.sha3_256(f.read_bytes()).hexdigest()
        mf.write('{0}  {1}\n'.format(h, f))
"

# 6. ACLs constitucionais
icacls C:\Arkhe\Substratos /inheritance:r /grant:r "Users:(RX)" /T
icacls C:\Arkhe\Proofs /grant:r "Users:(M)" /T
icacls C:\Arkhe\Logs /grant:r "Users:(M)" /T

# 7. Instalar serviço (modo Native)
if ($Mode -eq "Native") {
    & C:\Arkhe\venv\Scripts\python.exe C:\Arkhe\ArkheBridgeService.py install
    & C:\Arkhe\venv\Scripts\python.exe C:\Arkhe\ArkheBridgeService.py start
    Write-Host "Serviço ArkheBridge instalado." -ForegroundColor Green
}

# 8. Verificação inicial
& C:\Arkhe\venv\Scripts\python.exe C:\Arkhe\verify_constitution_windows.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "VERIFICAÇÃO CONSTITUCIONAL: PASS (Φ_C preservado)" -ForegroundColor Green
} else {
    Write-Host "VERIFICAÇÃO CONSTITUCIONAL: FAIL" -ForegroundColor Red
}