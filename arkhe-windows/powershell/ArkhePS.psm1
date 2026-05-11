# ARKHE OS - PowerShell Module
# Fornece cmdlets para interagir com o ARKHE no Windows

# Import C# DLL
Add-Type -Path "$PSScriptRoot\..\lib\arkhe_shared.dll"

function Get-ArkheStatus {
    <#
    .SYNOPSIS
        Obtém status do sistema ARKHE
    #>
    [CmdletBinding()]
    param()

    $driverLoaded = Get-Service -Name "ARKHE_Temporal" -ErrorAction SilentlyContinue

    return @{
        DriverLoaded = $driverLoaded -ne $null
        DriverState  = if ($driverLoaded) { $driverLoaded.Status } else { "NotInstalled" }
        ChainLength  = Get-ArkheChainLength
        OracleStatus = Get-Service -Name "arkhe-oracle" -ErrorAction SilentlyContinue |
                       Select-Object -ExpandProperty Status -ErrorAction SilentlyContinue
    }
}

function Get-ArkheChainLength {
    <#
    .SYNOPSIS
        Obtém o comprimento atual da cadeia temporal
    #>
    # Pode ser obtido via IOCTL ou do serviço
    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".",
            "ARKHE\Temporal", [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(1000)
        # ... enviar comando IOCTL via P/Invoke
        $pipe.Dispose()
        return 0  # Placeholder
    } catch {
        return -1
    }
}

function Get-ArkheRoute {
    <#
    .SYNOPSIS
        Encontra uma rota temporal entre dois nós
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Source,

        [Parameter(Mandatory=$true)]
        [string]$Destination,

        [switch]$Optimize
    )

    $cmd = "& '$env:ProgramFiles\ARKHE\arkhe-cli.exe' route $Source $Destination"
    if ($Optimize) { $cmd += " --optimize" }

    Invoke-Expression $cmd
}

function Get-ArkheConsensus {
    <#
    .SYNOPSIS
        Avalia o consenso de uma mensagem temporal
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$MessageId,

        [Parameter(Mandatory=$true)]
        [string]$Content
    )

    # Serializar mensagem
    $msg = @{
        id = $MessageId
        content = $Content
        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    } | ConvertTo-Json

    # Enviar ao oracle via named pipe
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".",
        "ARKHE\Oracle", [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)

    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.WriteLine($msg)
    $writer.Flush()

    $reader = New-Object System.IO.StreamReader($pipe)
    $response = $reader.ReadToEnd()

    $pipe.Dispose()

    return $response | ConvertFrom-Json
}

function Show-ArkheTopology {
    <#
    .SYNOPSIS
        Mostra a topologia do multiverso ARKHE
    #>
    try {
        & "$env:ProgramFiles\ARKHE\arkhe-cli.exe" status --format=visual
    } catch {
        Write-Error "Falha ao obter topologia"
    }
}

Export-ModuleMember -Function Get-ArkheStatus,
                         Get-ArkheRoute,
                         Get-ArkheConsensus,
                         Show-ArkheTopology
