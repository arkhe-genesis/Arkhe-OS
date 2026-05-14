# ArkheCmdlets.psm1 — Módulo PowerShell para Arkhe OS
function Get-ArkheStatus {
    <#
    .SYNOPSIS
    Retorna o status atual do Arkhe Runtime e da governança ASI.
    #>
    $service = Get-Service ArkheRuntime
    $phiC = (Invoke-RestMethod -Uri "http://localhost:9004/api/v1/health").phi_c_coherence
    [PSCustomObject]@{
        ServiceStatus = $service.Status
        PhiC = $phiC
        GovernanceActive = $true
        MeshPeers = (Invoke-RestMethod -Uri "http://localhost:9004/api/v1/mesh/peers").Count
        Uptime = (Get-Date) - (Get-Process ArkheService).StartTime
    }
}

function Invoke-ArkheAudit {
    <#
    .SYNOPSIS
    Executa uma auditoria de governança completa.
    #>
    param([string]$Path = $pwd)
    $result = & "$env:ProgramFiles\ArkheOS\arkh.exe" audit --path $Path --json
    $result | ConvertFrom-Json
}

function Install-ArkhePackage {
    <#
    .SYNOPSIS
    Instala um pacote do registry Arkhe com verificação ZK.
    #>
    param([string]$PackageName)
    & "$env:ProgramFiles\ArkheOS\arkh.exe" install $PackageName
}

function Start-ArkheGovernanceCycle {
    <#
    .SYNOPSIS
    Inicia um ciclo de governança Spiral Ping.
    #>
    & "$env:ProgramFiles\ArkheOS\arkh.exe" govern --ping-all
}

Export-ModuleMember -Function Get-ArkheStatus, Invoke-ArkheAudit,
                              Install-ArkhePackage, Start-ArkheGovernanceCycle
