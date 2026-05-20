// ═══════════════════════════════════════════════════════════════
// ARKHE OS — MICROSOFT DEFENDER FOR ENDPOINT INTEGRATION
// Canon: ∞.Ω.∇+++.310.mde_integration
// Detecção proativa de violações constitucionais via MDE custom rules
// ═══════════════════════════════════════════════════════════════
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using ArkheNode.Core;

namespace ArkheNode.Service;

/// <summary>
/// Integração com Microsoft Defender for Endpoint para detecção proativa
/// de violações constitucionais via custom detection rules.
/// </summary>
public class MdeIntegration
{
    private readonly HttpClient _httpClient;
    private readonly string _tenantId;
    private readonly string _clientId;
    private readonly string _clientSecret;
    private readonly string _mdeApiEndpoint;

    /// <summary>
    /// Inicializa integração com MDE.
    /// </summary>
    public MdeIntegration(
        string tenantId,
        string clientId,
        string clientSecret,
        string mdeApiEndpoint = "https://api.securitycenter.microsoft.com")
    {
        _tenantId = tenantId;
        _clientId = clientId;
        _clientSecret = clientSecret;
        _mdeApiEndpoint = mdeApiEndpoint;
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(mdeApiEndpoint),
            Timeout = TimeSpan.FromSeconds(30)
        };
    }

    /// <summary>
    /// Reporta violação constitucional para MDE como alerta personalizado.
    /// </summary>
    public async Task<bool> ReportConstitutionalViolationAsync(
        string nodeId,
        string invariantName,
        double actualValue,
        double threshold,
        string context = null)
    {
        try
        {
            // Obter token de acesso
            var accessToken = await GetAccessTokenAsync();
            _httpClient.DefaultRequestHeaders.Authorization =
                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", accessToken);

            // Criar alerta personalizado conforme schema MDE
            var alert = new MdeCustomAlert
            {
                Title = $"Constitutional Violation: {invariantName}",
                Category = "Arkhe Constitutional Compliance",
                Severity = actualValue < threshold * 0.8 ? "High" : "Medium",
                Description = $"Node {nodeId} violated {invariantName} invariant: " +
                             $"actual={actualValue:F4}, threshold={threshold:F4}. " +
                             (context != null ? $"Context: {context}" : ""),
                RecommendedActions = new[]
                {
                    "Review node configuration",
                    "Check network connectivity",
                    "Verify cryptographic module integrity",
                    "Consider isolating node if violation persists"
                },
                Entities = new[]
                {
                    new MdeAlertEntity
                    {
                        Type = "machine",
                        Value = nodeId
                    },
                    new MdeAlertEntity
                    {
                        Type = "file",
                        Value = "ArkheNode.Core.dll"
                    }
                },
                AdditionalFields = new Dictionary<string, object>
                {
                    ["Arkhe.Substrate"] = "310",
                    ["Arkhe.Invariant"] = invariantName,
                    ["Arkhe.ActualValue"] = actualValue,
                    ["Arkhe.Threshold"] = threshold,
                    ["Arkhe.PhiC"] = actualValue, // Φ_C como métrica de saúde
                    ["Arkhe.CanonicalSeal"] = GenerateViolationSeal(nodeId, invariantName, actualValue)
                }
            };

            // Enviar alerta para MDE
            var response = await _httpClient.PostAsJsonAsync(
                "/api/alerts", alert,
                new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

            response.EnsureSuccessStatusCode();

            // Ancorar reporte na TemporalChain para auditoria
            await AnchorViolationReportAsync(nodeId, invariantName, alert);

            return true;
        }
        catch (Exception ex)
        {
            // Fallback: registrar em log local se MDE indisponível
            Console.Error.WriteLine($"⚠️  Failed to report to MDE: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Registra regra de detecção personalizada no MDE via API.
    /// </summary>
    public async Task<bool> RegisterDetectionRuleAsync(ConstitutionalDetectionRule rule)
    {
        try
        {
            var accessToken = await GetAccessTokenAsync();
            _httpClient.DefaultRequestHeaders.Authorization =
                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", accessToken);

            var mdeRule = new MdeDetectionRule
            {
                Name = rule.RuleName,
                Description = rule.Description,
                Severity = rule.Severity,
                Category = "Arkhe Constitutional Compliance",
                Query = GenerateKqlQuery(rule),
                Enabled = true,
                AlertTitle = rule.AlertTitle,
                AlertDescription = rule.AlertDescription
            };

            var response = await _httpClient.PostAsJsonAsync(
                "/api/rules/detection", mdeRule,
                new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

            response.EnsureSuccessStatusCode();
            return true;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"⚠️  Failed to register MDE rule: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Gera query KQL para detecção de violações constitucionais.
    /// </summary>
    private string GenerateKqlQuery(ConstitutionalDetectionRule rule)
    {
        // Exemplo de query para detecção de Φ_C baixo
        return $@"
Event
| where ProviderName == ""ArkheNode-Core""
| where EventID == {rule.EventId}
| extend NodeId = tostring(parse_json(EventData).NodeId)
| extend PhiC = todouble(parse_json(EventData).PhiCValue)
| where PhiC < {rule.Threshold}
| summarize ViolationCount = count(), AvgPhiC = avg(PhiC) by NodeId, bin(TimeGenerated, 5m)
| where ViolationCount >= {rule.MinOccurrences}
| extend AlertReason = strcat(""Constitutional violation: Φ_C="", tostring(AvgPhiC))
";
    }

    /// <summary>
    /// Gera selo canônico para reporte de violação.
    /// </summary>
    private string GenerateViolationSeal(string nodeId, string invariant, double value)
    {
        var payload = new
        {
            nodeId,
            invariant,
            value,
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
            substrate = "310"
        };

        var json = JsonSerializer.Serialize(payload);
        // Using SHA256 for basic simulation instead of BouncyCastleSha3 to avoid missing deps during standalone compile
        var hash = System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(json));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    /// <summary>
    /// Ancora reporte de violação na TemporalChain.
    /// </summary>
    private async Task AnchorViolationReportAsync(string nodeId, string invariant, MdeCustomAlert alert)
    {
        // Mock: em produção, POST para endpoint da TemporalChain
        var anchorPayload = new
        {
            event_type = "constitutional_violation_reported",
            node_id = nodeId,
            invariant = invariant,
            mde_alert_id = alert.Title, // Mock ID
            canonical_seal = GenerateViolationSeal(nodeId, invariant, 0.0),
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
        };

        // Simular ancoragem
        await Task.Delay(10); // Mock delay
        Console.WriteLine($"🔗 Violation report anchored to TemporalChain: {nodeId}/{invariant}");
    }

    /// <summary>
    /// Obtém token de acesso OAuth2 para API do MDE.
    /// </summary>
    private async Task<string> GetAccessTokenAsync()
    {
        // Mock: em produção, usar Microsoft.Identity.Client para fluxo OAuth2
        // https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/exposed-apis-create-app-webapp
        await Task.Delay(10); // Mock delay
        return "mock_access_token_for_mde_api";
    }
}

/// <summary>
/// Regra de detecção constitucional para MDE.
/// </summary>
public record ConstitutionalDetectionRule
{
    public string RuleName { get; init; } = string.Empty;
    public string Description { get; init; } = string.Empty;
    public string Severity { get; init; } = "Medium"; // Low, Medium, High, Informational
    public int EventId { get; init; } // ID do evento ETW correspondente
    public double Threshold { get; init; } // Limiar para disparo da regra
    public int MinOccurrences { get; init; } = 1; // Mínimo de ocorrências para alerta
    public string AlertTitle { get; init; } = string.Empty;
    public string AlertDescription { get; init; } = string.Empty;
}

/// <summary>
/// Schema de alerta personalizado para MDE.
/// </summary>
public record MdeCustomAlert
{
    public string Title { get; init; } = string.Empty;
    public string Category { get; init; } = string.Empty;
    public string Severity { get; init; } = "Medium";
    public string Description { get; init; } = string.Empty;
    public string[] RecommendedActions { get; init; } = Array.Empty<string>();
    public MdeAlertEntity[] Entities { get; init; } = Array.Empty<MdeAlertEntity>();
    public Dictionary<string, object> AdditionalFields { get; init; } = new();
}

/// <summary>
/// Entidade de alerta MDE.
/// </summary>
public record MdeAlertEntity
{
    public string Type { get; init; } = string.Empty; // machine, file, ip, url, etc.
    public string Value { get; init; } = string.Empty;
}

/// <summary>
/// Schema de regra de detecção MDE.
/// </summary>
public record MdeDetectionRule
{
    public string Name { get; init; } = string.Empty;
    public string Description { get; init; } = string.Empty;
    public string Severity { get; init; } = "Medium";
    public string Category { get; init; } = string.Empty;
    public string Query { get; init; } = string.Empty; // KQL query
    public bool Enabled { get; init; } = true;
    public string AlertTitle { get; init; } = string.Empty;
    public string AlertDescription { get; init; } = string.Empty;
}