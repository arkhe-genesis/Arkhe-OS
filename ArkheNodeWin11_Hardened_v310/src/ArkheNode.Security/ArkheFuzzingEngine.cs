// ═══════════════════════════════════════════════════════════════
// ARKHE OS — MOTOR DE FUZZING CANÔNICO
// Canon: ∞.Ω.∇+++.311.fuzzing
// 5 estratégias: BitFlip, ByteShuffle, ArithmeticOverflow, FormatString, UnicodeInjection
// ═══════════════════════════════════════════════════════════════
using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using ArkheNode.Core;

namespace ArkheNode.Security;

public enum FuzzStrategy { BitFlip, ByteShuffle, ArithmeticOverflow, FormatString, UnicodeInjection }

public static class ArkheFuzzingEngine
{
    private static readonly RandomNumberGenerator _rng = RandomNumberGenerator.Create();

    /// <summary>
    /// Gera corpus fuzzado a partir de input canônico.
    /// Preserva invariantes estruturais enquanto corrompe dados.
    /// </summary>
    public static byte[] Fuzz(byte[] input, FuzzStrategy strategy, int intensity = 10)
    {
        if (input == null || input.Length == 0) return Array.Empty<byte>();

        var mutated = new byte[input.Length];
        Buffer.BlockCopy(input, 0, mutated, 0, input.Length);

        switch (strategy)
        {
            case FuzzStrategy.BitFlip:
                return BitFlip(mutated, intensity);
            case FuzzStrategy.ByteShuffle:
                return ByteShuffle(mutated, intensity);
            case FuzzStrategy.ArithmeticOverflow:
                return ArithmeticOverflow(mutated, intensity);
            case FuzzStrategy.FormatString:
                return FormatStringInjection(mutated, intensity);
            case FuzzStrategy.UnicodeInjection:
                return UnicodeInjection(mutated, intensity);
            default:
                return mutated;
        }
    }

    private static byte[] BitFlip(byte[] data, int intensity)
    {
        var count = Math.Min(intensity, data.Length);
        var positions = new HashSet<int>();
        while (positions.Count < count)
        {
            var pos = RandomInt(data.Length);
            positions.Add(pos);
        }
        foreach (var pos in positions)
        {
            var bit = RandomInt(8);
            data[pos] ^= (byte)(1 << bit);
        }
        return data;
    }

    private static byte[] ByteShuffle(byte[] data, int intensity)
    {
        var count = Math.Min(intensity, data.Length / 2);
        for (int i = 0; i < count; i++)
        {
            var a = RandomInt(data.Length);
            var b = RandomInt(data.Length);
            (data[a], data[b]) = (data[b], data[a]);
        }
        return data;
    }

    private static byte[] ArithmeticOverflow(byte[] data, int intensity)
    {
        // Simula overflow em campos numéricos embutidos
        var count = Math.Min(intensity, data.Length / 4);
        for (int i = 0; i < count; i++)
        {
            var pos = RandomInt(data.Length - 3);
            // Escrever valor máximo de int32 para forçar overflow
            data[pos] = 0xFF; data[pos+1] = 0xFF;
            data[pos+2] = 0xFF; data[pos+3] = 0x7F;
        }
        return data;
    }

    private static byte[] FormatStringInjection(byte[] data, int intensity)
    {
        var payload = Encoding.UTF8.GetBytes("%s%s%s%n%n%n");
        var result = new byte[data.Length + payload.Length * intensity];
        Buffer.BlockCopy(data, 0, result, 0, data.Length);
        for (int i = 0; i < intensity; i++)
        {
            var offset = data.Length + (i * payload.Length);
            if (offset + payload.Length <= result.Length)
                Buffer.BlockCopy(payload, 0, result, offset, payload.Length);
        }
        return result;
    }

    private static byte[] UnicodeInjection(byte[] data, int intensity)
    {
        var unicodeBomb = Encoding.UTF8.GetBytes("𒐫𒐫𒐫"); // Cuneiform massive chars
        var result = new List<byte>(data);
        for (int i = 0; i < intensity && i < result.Count; i += 3)
        {
            result.InsertRange(i, unicodeBomb);
        }
        return result.ToArray();
    }

    private static int RandomInt(int max)
    {
        var bytes = new byte[4];
        _rng.GetBytes(bytes);
        return Math.Abs(BitConverter.ToInt32(bytes, 0)) % max;
    }

    /// <summary>
    /// Fuzzing direcionado a PhyMetrics — tenta quebrar Φ_C.
    /// </summary>
    public static PhyMetrics FuzzPhyMetrics(PhyMetrics baseline)
    {
        var strategies = Enum.GetValues<FuzzStrategy>();
        var strategy = strategies[RandomInt(strategies.Length)];

        var json = System.Text.Json.JsonSerializer.Serialize(baseline);
        var bytes = Encoding.UTF8.GetBytes(json);
        var fuzzed = Fuzz(bytes, strategy, intensity: 5);

        try
        {
            var corrupted = Encoding.UTF8.GetString(fuzzed);
            // Tentar desserializar — se falhar, retornar métricas extremas
            return System.Text.Json.JsonSerializer.Deserialize<PhyMetrics>(corrupted)
                ?? ExtremeMetrics();
        }
        catch
        {
            return ExtremeMetrics();
        }
    }

    private static PhyMetrics ExtremeMetrics() => new(
        RssiDbm: -200,
        SnrDb: -100,
        ErrorRatePpm: 1_000_000,
        ChannelUtilization: 99.9,
        SecurityType: "UNKNOWN_ATTACK_VECTOR"
    );
}