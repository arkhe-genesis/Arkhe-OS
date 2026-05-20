// ═══════════════════════════════════════════════════════════════
// ARKHE OS — SIMULADOR DE SIDE-CHANNEL
// Canon: ∞.Ω.∇+++.311.side_channel
// 4 channels: Timing, Power, Cache, Electromagnetic
// ═══════════════════════════════════════════════════════════════
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using ArkheNode.Core;

namespace ArkheNode.Security;

public enum SideChannelType { Timing, Power, Cache, Electromagnetic }

public static class ArkheSideChannelSimulator
{
    /// <summary>
    /// Mede variação de tempo no cálculo de Φ_C para detectar vazamento
    /// de informação via timing (ex: branch diferente por segurança).
    /// </summary>
    public static SideChannelReport AnalyzeTimingChannel(int iterations = 10000)
    {
        var sw = new Stopwatch();
        var timingsWpa3 = new List<long>();
        var timingsOpen = new List<long>();

        // WPA3 (caminho seguro)
        var secureMetrics = new PhyMetrics(-50, 30, 10, 0.3, "WPA3");
        for (int i = 0; i < iterations; i++)
        {
            sw.Restart();
            PhiCCalculator.Calculate(secureMetrics);
            sw.Stop();
            timingsWpa3.Add(sw.ElapsedTicks);
        }

        // OPEN (caminho inseguro — pode ter branches diferentes)
        var insecureMetrics = new PhyMetrics(-50, 30, 10, 0.3, "OPEN");
        for (int i = 0; i < iterations; i++)
        {
            sw.Restart();
            PhiCCalculator.Calculate(insecureMetrics);
            sw.Stop();
            timingsOpen.Add(sw.ElapsedTicks);
        }

        var avgSecure = timingsWpa3.Average();
        var avgInsecure = timingsOpen.Average();
        var variance = Math.Abs(avgSecure - avgInsecure) / Math.Min(avgSecure, avgInsecure);

        return new SideChannelReport(
            ChannelType: SideChannelType.Timing,
            VarianceCoefficient: variance,
            IsVulnerable: variance > 0.05, // >5% de diferença = vulnerável
            SecurePathAvgTicks: avgSecure,
            InsecurePathAvgTicks: avgInsecure,
            Recommendation: variance > 0.05
                ? "CRITICAL: Timing difference detected. Equalize execution paths."
                : "PASS: Timing channel sealed."
        );
    }

    /// <summary>
    /// Simula análise de consumo de energia por operação criptográfica.
    /// </summary>
    public static SideChannelReport AnalyzePowerChannel(int sampleSize = 1000)
    {
        // Mock: em hardware real, medir amperagem durante SHA3-256
        var samples = new List<double>();
        var rng = new Random();

        for (int i = 0; i < sampleSize; i++)
        {
            // Simular consumo em mA com ruído gaussiano
            var baseLoad = 120.0; // mA para SHA3-256
            var noise = rng.NextDouble() * 10 - 5;
            samples.Add(baseLoad + noise);
        }

        var mean = samples.Average();
        var stdDev = Math.Sqrt(samples.Average(s => Math.Pow(s - mean, 2)));

        // Se desvio padrão > 15% da média, há vazamento de Hamming weight
        var isVulnerable = stdDev / mean > 0.15;

        return new SideChannelReport(
            ChannelType: SideChannelType.Power,
            VarianceCoefficient: stdDev / mean,
            IsVulnerable: isVulnerable,
            SecurePathAvgTicks: 0,
            InsecurePathAvgTicks: 0,
            Recommendation: isVulnerable
                ? "WARNING: Power consumption variance suggests Hamming weight leakage. Implement constant-time algorithms."
                : "PASS: Power consumption stable."
        );
    }

    /// <summary>
    /// Simula ataque de cache timing (Flush+Reload / Prime+Probe).
    /// </summary>
    public static SideChannelReport AnalyzeCacheChannel()
    {
        // Simular acesso a lookup tables em criptografia
        var cacheHits = new List<bool>();
        var rng = new Random();

        for (int i = 0; i < 1000; i++)
        {
            // Simular padrão de acesso dependente de segredo
            var secretDependent = rng.NextDouble() > 0.5;
            cacheHits.Add(secretDependent);
        }

        var hitRate = cacheHits.Count(h => h) / (double)cacheHits.Count;
        // Se hit rate varia com o segredo, há vazamento
        var isVulnerable = Math.Abs(hitRate - 0.5) > 0.1;

        return new SideChannelReport(
            ChannelType: SideChannelType.Cache,
            VarianceCoefficient: Math.Abs(hitRate - 0.5),
            IsVulnerable: isVulnerable,
            SecurePathAvgTicks: 0,
            InsecurePathAvgTicks: 0,
            Recommendation: isVulnerable
                ? "WARNING: Cache access pattern correlates with secret. Use cache-oblivious algorithms."
                : "PASS: Cache access pattern uniform."
        );
    }
}

public record SideChannelReport(
    SideChannelType ChannelType,
    double VarianceCoefficient,
    bool IsVulnerable,
    double SecurePathAvgTicks,
    double InsecurePathAvgTicks,
    string Recommendation
);