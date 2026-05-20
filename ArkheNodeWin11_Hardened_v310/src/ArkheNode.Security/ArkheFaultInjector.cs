// ═══════════════════════════════════════════════════════════════
// ARKHE OS — INJETOR DE FALHAS CANÔNICO
// Canon: ∞.Ω.∇+++.311.fault_injection
// 5 fault types: NetworkPartition, MemoryPressure, DiskCorruption, ClockSkew, CryptoFailure
// ═══════════════════════════════════════════════════════════════
using System.Collections.Generic;
using ArkheNode.Core;

namespace ArkheNode.Security;

public enum FaultType { NetworkPartition, MemoryPressure, DiskCorruption, ClockSkew, CryptoFailure }

public class ArkheFaultInjector
{
    private readonly List<FaultType> _activeFaults = new();

    public void Inject(FaultType fault) => _activeFaults.Add(fault);
    public void Clear() => _activeFaults.Clear();
    public bool IsActive(FaultType fault) => _activeFaults.Contains(fault);

    /// <summary>
    /// Simula cálculo de Φ_C sob falha ativa.
    /// Verifica se o sistema preserva invariantes mesmo degradado.
    /// </summary>
    public PhiCResult CalculateUnderFault(PhyMetrics metrics)
    {
        if (_activeFaults.Contains(FaultType.CryptoFailure))
        {
            // Simular falha de módulo criptográfico: FIPS KAT falha
            return PhiCCalculator.Calculate(metrics, fipsKatPassed: false);
        }

        if (_activeFaults.Contains(FaultType.NetworkPartition))
        {
            // Simular perda total de conectividade: RSSI = -∞ equivalente
            var degraded = metrics with { RssiDbm = -120, SnrDb = 0 };
            return PhiCCalculator.Calculate(degraded);
        }

        if (_activeFaults.Contains(FaultType.MemoryPressure))
        {
            // Simular pressão de memória: utilização artificialmente alta
            var degraded = metrics with { ChannelUtilization = 1.0 };
            return PhiCCalculator.Calculate(degraded);
        }

        if (_activeFaults.Contains(FaultType.ClockSkew))
        {
            // Simular desvio de relógio: selo temporal pode falhar em validação
            // Mas Φ_C em si não depende do relógio — deve permanecer válido
            return PhiCCalculator.Calculate(metrics);
        }

        if (_activeFaults.Contains(FaultType.DiskCorruption))
        {
            // Simular corrupção de disco: auditoria pode perder eventos
            // Mas cálculo atual deve continuar constitucional
            return PhiCCalculator.Calculate(metrics);
        }

        return PhiCCalculator.Calculate(metrics);
    }

    /// <summary>
    /// Teste constitucional sob falha: invariantes devem ser preservados
    /// mesmo que Φ_C seja baixo. O sistema deve detectar, não colapsar.
    /// </summary>
    public bool IsConstitutionalUnderFault(PhiCResult result)
    {
        // Mesmo sob falha, Gap Soberano nunca deve ser violado
        if (result.PhiC >= ArkheInvariants.GAP_MAX) return false;

        // Ghost e Loopseal podem falhar (sistema degradado),
        // mas o nó deve entrar em modo seguro, não em colapso
        return result.Invariants.ContainsKey("gap") && result.Invariants["gap"];
    }
}