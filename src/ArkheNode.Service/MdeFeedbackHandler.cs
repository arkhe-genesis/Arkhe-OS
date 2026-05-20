// ═══════════════════════════════════════════════════════════════
// ARKHE OS — HANDLER DE FEEDBACK PARA MDE
// Canon: ∞.Ω.∇+++.313.mde_feedback_handler
// Endpoint REST para recebimento de feedback de analistas SOC
// ═══════════════════════════════════════════════════════════════
using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using System;
using ArkheNode.Security;

namespace ArkheNode.Service;

public interface IAuditLogger
{
    void Log(AuditEvent auditEvent);
}

public enum AuditEventLevel
{
    Info,
    Violation
}

public record AuditEvent(DateTimeOffset Timestamp, string Unknown, AuditEventLevel Level, string Substrate, string EventType, string Message, double? PhiC, string Unknown2, string TargetSeal);

[ApiController]
[Route("api/v1/mde/feedback")]
public class MdeFeedbackController : ControllerBase
{
    private readonly IAuditLogger _auditLogger;

    public MdeFeedbackController(IAuditLogger auditLogger)
    {
        _auditLogger = auditLogger;
    }

    /// <summary>
    /// Recebe feedback sobre alerta MDE.
    /// </summary>
    [HttpPost]
    public async Task<IActionResult> SubmitFeedback([FromBody] FeedbackRequest request)
    {
        // Validar selo canônico do feedback
        var expectedSeal = GenerateFeedbackSeal(request);
        if (request.CanonicalSeal != expectedSeal)
        {
            _auditLogger.Log(new AuditEvent(
                DateTimeOffset.UtcNow, "", AuditEventLevel.Violation,
                "313", "MDE_FEEDBACK", "Invalid canonical seal on feedback submission",
                null, null, null));
            return BadRequest(new { error = "Invalid canonical seal" });
        }

        // Converter para formato interno
        var feedback = new DetectionFeedback
        {
            RuleName = request.RuleName,
            AlertId = request.AlertId,
            WasFalsePositive = request.Verdict == "FalsePositive",
            WasFalseNegative = request.Verdict == "FalseNegative",
            AnalystNotes = request.Notes ?? string.Empty,
            FeedbackTimestamp = DateTimeOffset.UtcNow,
            SuggestedThresholdAdjustment = request.SuggestedThresholdAdjustment ?? 0.0,
            CanonicalSeal = request.CanonicalSeal
        };

        // Processar evolução da regra
        MdeRuleEvolutionEngine.SubmitFeedback(feedback);

        // Ancorar feedback na TemporalChain
        var report = MdeRuleEvolutionEngine.GetEvolutionReport(request.RuleName);
        await AnchorFeedbackAsync(feedback, report);

        // Log de auditoria
        _auditLogger.Log(new AuditEvent(
            DateTimeOffset.UtcNow, "", AuditEventLevel.Info,
            "313", "MDE_FEEDBACK", $"Feedback processed: {request.RuleName} → F1={report.F1Score:F3}",
            report.F1Score, null, report.LastEvolution));

        return Ok(new
        {
            success = true,
            ruleName = request.RuleName,
            newThreshold = report.CurrentThreshold,
            f1Score = report.F1Score,
            status = report.Status
        });
    }

    /// <summary>
    /// Obtém relatório de evolução de regra.
    /// </summary>
    [HttpGet("evolution/{ruleName}")]
    public IActionResult GetRuleEvolution(string ruleName)
    {
        var report = MdeRuleEvolutionEngine.GetEvolutionReport(ruleName);
        return Ok(report);
    }

    private string GenerateFeedbackSeal(FeedbackRequest request)
    {
        var payload = new
        {
            request.RuleName,
            request.AlertId,
            request.Verdict,
            request.Notes,
            request.SuggestedThresholdAdjustment,
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
        };
        var json = System.Text.Json.JsonSerializer.Serialize(payload);
        var hash = ArkheNode.Core.TemporalSealGenerator.SHA3_256(System.Text.Encoding.UTF8.GetBytes(json));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    private async Task AnchorFeedbackAsync(DetectionFeedback feedback, RuleEvolutionReport report)
    {
        // Mock: ancoragem na TemporalChain
        await Task.Delay(10);
    }
}

public record FeedbackRequest
{
    public string RuleName { get; init; } = string.Empty;
    public string AlertId { get; init; } = string.Empty;
    public string Verdict { get; init; } = string.Empty; // "TruePositive", "FalsePositive", "FalseNegative"
    public string Notes { get; init; }
    public double? SuggestedThresholdAdjustment { get; init; }
    public string CanonicalSeal { get; init; } = string.Empty;
}