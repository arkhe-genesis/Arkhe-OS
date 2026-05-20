// ═══════════════════════════════════════════════════════════════
// ARKHE OS — SENTINELONE INTEGRATION ADAPTER
// Canon: ∞.Ω.∇+++.313.sentinelone
// REST API 2.1 + Webhook — 7 regras canônicas mapeadas
// ═══════════════════════════════════════════════════════════════
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using ArkheNode.Core;

namespace ArkheNode.Security;

/// <summary>
/// Adaptador canônico para SentinelOne Singularity Platform.
/// Traduz eventos Arkhe para schema SentinelOne preservando invariância.
/// </summary>
public class ArkheSentinelOneAdapter
{
    private readonly HttpClient _httpClient;
    private readonly string _apiToken;
    private readonly string _managementUrl;
    private readonly string _siteId;

    public ArkheSentinelOneAdapter(
        string managementUrl,
        string apiToken,
        string siteId)
    {
        _managementUrl = managementUrl.TrimEnd('/');
        _apiToken = apiToken;
        _siteId = siteId;
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri($"{_managementUrl}/web/api/v2.1/"),
            Timeout = TimeSpan.FromSeconds(30)
        };
        _httpClient.DefaultRequestHeaders.Add("Authorization", $"ApiToken {_apiToken}");
    }

    /// <summary>
    /// Reporta violação constitucional para SentinelOne como Threat Intel.
    /// </summary>
    public async Task<bool> ReportConstitutionalViolationAsync(
        string nodeId,
        string invariantName,
        double phiC,
        string violationType)
    {
        try
        {
            // Traduzir evento Arkhe para schema SentinelOne
            var sentinelEvent = new SentinelOneThreatEvent
            {
                Data = new SentinelOneEventData
                {
                    AgentDetectionInfo = new AgentDetectionInfo
                    {
                        AgentName = nodeId,
                        SiteName = "Arkhe-Federation",
                        CustomTags = new Dictionary<string, string>
                        {
                            ["arkhe_substrate"] = "313",
                            ["arkhe_invariant"] = invariantName,
                            ["arkhe_phi_c"] = phiC.ToString("F4"),
                            ["arkhe_constitutional"] = (phiC >= ArkheInvariants.GHOST).ToString()
                        }
                    },
                    ThreatInfo = new ThreatInfo
                    {
                        ThreatName = $"Arkhe-{violationType}",
                        Classification = "ConstitutionalViolation",
                        Severity = MapSeverity(phiC, invariantName),
                        ConfidenceLevel = "high"
                    }
                }
            };

            // Enviar para SentinelOne
            var response = await _httpClient.PostAsJsonAsync(
                "threats", sentinelEvent);

            response.EnsureSuccessStatusCode();

            // Disparar auto-remediação se necessário
            if (phiC < ArkheInvariants.GHOST || violationType == "SealTampering")
            {
                await TriggerAutoRemediationAsync(nodeId, violationType);
            }

            return true;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"⚠️  SentinelOne report failed: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Registra regra de detecção customizada no SentinelOne.
    /// </summary>
    public async Task<bool> RegisterDetectionRuleAsync(ConstitutionalDetectionRule rule)
    {
        try
        {
            var s1Rule = new SentinelOneCustomRule
            {
                Name = $"Arkhe-{rule.RuleName}",
                Description = rule.Description,
                Severity = MapToS1Severity(rule.Severity),
                Query = TranslateToS1Query(rule),
                SiteIds = new[] { _siteId },
                Status = "active"
            };

            var response = await _httpClient.PostAsJsonAsync(
                "custom-detection-rules", s1Rule);

            response.EnsureSuccessStatusCode();
            return true;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"⚠️  SentinelOne rule registration failed: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Dispara auto-remediação canônica no SentinelOne.
    /// </summary>
    private async Task TriggerAutoRemediationAsync(string nodeId, string violationType)
    {
        var actions = new List<string>();

        switch (violationType)
        {
            case "SealTampering":
            case "AutocideBreach":
                actions.Add("isolate-agent");
                actions.Add("kill-process");
                break;
            case "GhostViolation":
            case "LoopsealViolation":
                actions.Add("quarantine-file");
                break;
            case "ETWDisable":
                actions.Add("kill-process");
                break;
        }

        foreach (var action in actions)
        {
            try
            {
                var response = await _httpClient.PostAsJsonAsync(
                    $"agents/actions/{action}",
                    new { Filter = new { ComputerName = nodeId } });
                response.EnsureSuccessStatusCode();
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Remediation action {action} failed: {ex.Message}");
            }
        }
    }

    private string MapSeverity(double phiC, string invariant)
    {
        if (invariant == "SealTampering" || invariant == "Autocide") return "Critical";
        if (phiC < ArkheInvariants.GHOST * 0.8) return "High";
        if (phiC < ArkheInvariants.GHOST) return "Medium";
        return "Low";
    }

    private string MapToS1Severity(string arkheSeverity) => arkheSeverity switch
    {
        "Critical" => "Critical",
        "High" => "High",
        "Medium" => "Medium",
        _ => "Low"
    };

    /// <summary>
    /// Traduz query KQL Arkhe para query Star Query Language (S1QL).
    /// </summary>
    private string TranslateToS1Query(ConstitutionalDetectionRule rule)
    {
        // S1QL: SentinelOne Query Language
        return rule.RuleName switch
        {
            "ConstitutionalViolation_Ghost" =>
                "AgentName Contains 'Arkhe' AND CustomTags.arkhe_phi_c < 0.577350",
            "ConstitutionalViolation_Loopseal" =>
                "AgentName Contains 'Arkhe' AND CustomTags.arkhe_invariant = 'LOOPSEAL'",
            "ConstitutionalViolation_Gap" =>
                "AgentName Contains 'Arkhe' AND CustomTags.arkhe_phi_c >= 0.9999",
            "PhiC_Critical_Degradation" =>
                "AgentName Contains 'Arkhe' AND CustomTags.arkhe_phi_c < 0.70",
            "Seal_Tampering_Detected" =>
                "AgentName Contains 'Arkhe' AND ThreatName Contains 'Tampering'",
            "Autocide_Threshold_Breach" =>
                "AgentName Contains 'Arkhe' AND ThreatName Contains 'Autocide'",
            "ETW_Provider_Disable_Attempt" =>
                "ProcessName Contains 'Arkhe' AND EventType = 'ProcessTampering'",
            _ => $"AgentName Contains 'Arkhe' AND CustomTags.arkhe_invariant = '{rule.RuleName}'"
        };
    }
}

// Schemas SentinelOne
public record SentinelOneThreatEvent { public SentinelOneEventData Data { get; init; } }
public record SentinelOneEventData
{
    public AgentDetectionInfo AgentDetectionInfo { get; init; }
    public ThreatInfo ThreatInfo { get; init; }
}
public record AgentDetectionInfo
{
    public string AgentName { get; init; }
    public string SiteName { get; init; }
    public Dictionary<string, string> CustomTags { get; init; }
}
public record ThreatInfo
{
    public string ThreatName { get; init; }
    public string Classification { get; init; }
    public string Severity { get; init; }
    public string ConfidenceLevel { get; init; }
}
public record SentinelOneCustomRule
{
    public string Name { get; init; }
    public string Description { get; init; }
    public string Severity { get; init; }
    public string Query { get; init; }
    public string[] SiteIds { get; init; }
    public string Status { get; init; }
}