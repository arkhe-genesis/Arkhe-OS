// ═══════════════════════════════════════════════════════════════
// ARKHE OS — MOTOR DE EVOLUÇÃO DE REGRAS MDE
// Canon: ∞.Ω.∇+++.313.mde_rule_evolution
// Aprendizado canônico: falsos positivos/negativos → refinamento de thresholds
// ═══════════════════════════════════════════════════════════════
using System.Collections.Concurrent;
using System.Text.Json;

namespace ArkheNode.Security;

/// <summary>
/// Representa feedback sobre uma detecção MDE.
/// </summary>
public record DetectionFeedback
{
    public string RuleName { get; init; } = string.Empty;
    public string AlertId { get; init; } = string.Empty;
    public bool WasFalsePositive { get; init; }
    public bool WasFalseNegative { get; init; }
    public string AnalystNotes { get; init; } = string.Empty;
    public DateTimeOffset FeedbackTimestamp { get; init; }
    public double SuggestedThresholdAdjustment { get; init; } // -0.1 a +0.1
    public string CanonicalSeal { get; init; } = string.Empty; // SHA3-256 do feedback
}

/// <summary>
/// Estado evolutivo de uma regra de detecção.
/// </summary>
public record RuleEvolutionState
{
    public string RuleName { get; init; } = string.Empty;
    public double CurrentThreshold { get; init; }
    public double OriginalThreshold { get; init; }
    public int TotalDetections { get; init; }
    public int FalsePositives { get; init; }
    public int FalseNegatives { get; init; }
    public double Precision => TotalDetections > 0 ? (double)(TotalDetections - FalsePositives) / TotalDetections : 1.0;
    public double Recall => TotalDetections > 0 ? (double)(TotalDetections - FalseNegatives) / TotalDetections : 1.0;
    public double F1Score => Precision + Recall > 0 ? 2 * Precision * Recall / (Precision + Recall) : 0.0;
    public DateTimeOffset LastUpdated { get; init; }
    public List<string> EvolutionHistory { get; init; } = new(); // Selos de cada ajuste
}

/// <summary>
/// Motor de evolução de regras baseado em feedback canônico.
/// </summary>
public static class MdeRuleEvolutionEngine
{
    private static readonly ConcurrentDictionary<string, RuleEvolutionState> _ruleStates = new();
    private static readonly object _lock = new();

    // Thresholds canônicos iniciais (Substrato 312)
    private static readonly Dictionary<string, double> _canonicalThresholds = new()
    {
        ["Arkhe-Low-PhiC-Detection"] = 0.70,
        ["Arkhe-Invariant-Violation"] = 0.0,
        ["Arkhe-Seal-Tampering"] = 0.0,
        ["Arkhe-PhiC-Degradation"] = 0.20, // 20% degradation threshold
        ["Arkhe-Autocide-Breach"] = 0.577350 // Ghost invariant
    };

    /// <summary>
    /// Inicializa estado evolutivo para uma regra.
    /// </summary>
    public static void InitializeRule(string ruleName)
    {
        if (_canonicalThresholds.TryGetValue(ruleName, out var threshold))
        {
            _ruleStates[ruleName] = new RuleEvolutionState
            {
                RuleName = ruleName,
                CurrentThreshold = threshold,
                OriginalThreshold = threshold,
                TotalDetections = 0,
                FalsePositives = 0,
                FalseNegatives = 0,
                LastUpdated = DateTimeOffset.UtcNow,
                EvolutionHistory = new() { GenerateEvolutionSeal(ruleName, threshold, "initial") }
            };
        }
    }

    /// <summary>
    /// Registra feedback sobre uma detecção.
    /// </summary>
    public static void SubmitFeedback(DetectionFeedback feedback)
    {
        if (!_ruleStates.ContainsKey(feedback.RuleName))
            InitializeRule(feedback.RuleName);

        lock (_lock)
        {
            if (!_ruleStates.TryGetValue(feedback.RuleName, out var state))
                return;

            // Atualizar contadores
            state = state with
            {
                TotalDetections = state.TotalDetections + 1,
                FalsePositives = feedback.WasFalsePositive ? state.FalsePositives + 1 : state.FalsePositives,
                FalseNegatives = feedback.WasFalseNegative ? state.FalseNegatives + 1 : state.FalseNegatives,
                LastUpdated = DateTimeOffset.UtcNow
            };

            // Calcular ajuste sugerido baseado em F1 Score
            if (state.F1Score < 0.85 && state.TotalDetections >= 10)
            {
                // Ajuste conservador: máximo ±0.05 por iteração
                var adjustment = Math.Clamp(feedback.SuggestedThresholdAdjustment, -0.05, 0.05);
                var newThreshold = Math.Clamp(
                    state.CurrentThreshold + adjustment,
                    GetMinThreshold(feedback.RuleName),
                    GetMaxThreshold(feedback.RuleName)
                );

                state = state with
                {
                    CurrentThreshold = newThreshold,
                    EvolutionHistory = state.EvolutionHistory.Append(
                        GenerateEvolutionSeal(feedback.RuleName, newThreshold, feedback.AnalystNotes)
                    ).ToList()
                };

                // Ancorar evolução na TemporalChain
                AnchorRuleEvolution(feedback.RuleName, state, feedback.CanonicalSeal);
            }

            _ruleStates[feedback.RuleName] = state;
        }
    }

    /// <summary>
    /// Obtém threshold atualizado para uma regra.
    /// </summary>
    public static double GetCurrentThreshold(string ruleName)
    {
        return _ruleStates.TryGetValue(ruleName, out var state)
            ? state.CurrentThreshold
            : _canonicalThresholds.GetValueOrDefault(ruleName, 0.0);
    }

    /// <summary>
    /// Gera KQL atualizado com threshold evolutivo.
    /// </summary>
    public static string GenerateUpdatedKql(string ruleName, string baseKql)
    {
        var threshold = GetCurrentThreshold(ruleName);

        // Substituir placeholder de threshold no KQL
        return baseKql.Replace("{THRESHOLD}", threshold.ToString("F6", System.Globalization.CultureInfo.InvariantCulture));
    }

    /// <summary>
    /// Obtém relatório de evolução para auditoria.
    /// </summary>
    public static RuleEvolutionReport GetEvolutionReport(string ruleName)
    {
        if (!_ruleStates.TryGetValue(ruleName, out var state))
            return new RuleEvolutionReport { RuleName = ruleName, Status = "NotInitialized" };

        return new RuleEvolutionReport
        {
            RuleName = ruleName,
            CurrentThreshold = state.CurrentThreshold,
            OriginalThreshold = state.OriginalThreshold,
            TotalDetections = state.TotalDetections,
            Precision = state.Precision,
            Recall = state.Recall,
            F1Score = state.F1Score,
            EvolutionCount = state.EvolutionHistory.Count - 1, // Exclui "initial"
            LastEvolution = state.EvolutionHistory.LastOrDefault(),
            Status = state.F1Score >= 0.90 ? "Optimized" :
                     state.F1Score >= 0.75 ? "Learning" : "NeedsReview"
        };
    }

    private static double GetMinThreshold(string ruleName) => ruleName switch
    {
        "Arkhe-Low-PhiC-Detection" => 0.50,
        "Arkhe-PhiC-Degradation" => 0.10,
        _ => 0.0
    };

    private static double GetMaxThreshold(string ruleName) => ruleName switch
    {
        "Arkhe-Low-PhiC-Detection" => 0.90,
        "Arkhe-PhiC-Degradation" => 0.50,
        _ => 1.0
    };

    private static string GenerateEvolutionSeal(string ruleName, double threshold, string notes)
    {
        var payload = new { ruleName, threshold, notes, timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() };
        var json = JsonSerializer.Serialize(payload);
        var hash = ArkheNode.Core.TemporalSealGenerator.SHA3_256(System.Text.Encoding.UTF8.GetBytes(json));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    private static void AnchorRuleEvolution(string ruleName, RuleEvolutionState state, string feedbackSeal)
    {
        // Mock: em produção, POST para TemporalChain
        var anchorPayload = new
        {
            event_type = "rule_evolution_anchored",
            rule_name = ruleName,
            new_threshold = state.CurrentThreshold,
            f1_score = state.F1Score,
            feedback_seal = feedbackSeal,
            evolution_seal = state.EvolutionHistory.Last(),
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
        };
        // TemporalChain.Anchor(anchorPayload);
    }
}

public record RuleEvolutionReport
{
    public string RuleName { get; init; } = string.Empty;
    public double CurrentThreshold { get; init; }
    public double OriginalThreshold { get; init; }
    public double ThresholdChange => CurrentThreshold - OriginalThreshold;
    public int TotalDetections { get; init; }
    public double Precision { get; init; }
    public double Recall { get; init; }
    public double F1Score { get; init; }
    public int EvolutionCount { get; init; }
    public string LastEvolution { get; init; }
    public string Status { get; init; } = string.Empty;
}