// ═══════════════════════════════════════════════════════════════
// ARKHE OS — CROWDSTRIKE INTEGRATION ADAPTER
// Canon: ∞.Ω.∇+++.313.crowdstrike
// Falcon API v1 + Real-time Response — 7 regras canônicas mapeadas
// ═══════════════════════════════════════════════════════════════
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using ArkheNode.Core;

namespace ArkheNode.Security;

/// <summary>
/// Adaptador canônico para CrowdStrike Falcon Platform.
/// Traduz eventos Arkhe para schema CrowdStrike via Custom IOAs.
/// </summary>
public class ArkheCrowdStrikeAdapter
{
    private readonly HttpClient _httpClient;
    private readonly string _clientId;
    private readonly string _clientSecret;
    private readonly string _baseUrl;
    private string _accessToken;
    private DateTime _tokenExpiry;

    public ArkheCrowdStrikeAdapter(
        string baseUrl,
        string clientId,
        string clientSecret)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _clientId = clientId;
        _clientSecret = clientSecret;
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri($"{_baseUrl}/"),
            Timeout = TimeSpan.FromSeconds(30)
        };
    }

    /// <summary>
    /// Obtém token OAuth2 para Falcon API.
    /// </summary>
    private async Task EnsureAccessTokenAsync()
    {
        if (!string.IsNullOrEmpty(_accessToken) && DateTime.UtcNow < _tokenExpiry)
            return;

        var authContent = new FormUrlEncodedContent(new[]
        {
            new KeyValuePair<string, string>("client_id", _clientId),
            new KeyValuePair<string, string>("client_secret", _clientSecret)
        });

        var response = await _httpClient.PostAsync(
            "oauth2/token", authContent);
        response.EnsureSuccessStatusCode();

        var tokenResponse = await response.Content.ReadFromJsonAsync<FalconTokenResponse>();
        _accessToken = tokenResponse.AccessToken;
        _tokenExpiry = DateTime.UtcNow.AddSeconds(tokenResponse.ExpiresIn - 60);
    }

    /// <summary>
    /// Reporta violação constitucional para CrowdStrike como Custom IOA.
    /// </summary>
    public async Task<bool> ReportConstitutionalViolationAsync(
        string nodeId,
        string invariantName,
        double phiC,
        string violationType)
    {
        await EnsureAccessTokenAsync();

        try
        {
            // Traduzir evento Arkhe para schema CrowdStrike IOA
            var ioaEvent = new CrowdStrikeIoAEvent
            {
                Event = new IoAEventDetail
                {
                    HostName = nodeId,
                    PlatformName = "Arkhe-313",
                    IOAName = $"Arkhe-{invariantName}",
                    IOADescription = $"Constitutional violation: {violationType} | PhiC={phiC:F4}",
                    Severity = MapToFalconSeverity(phiC, violationType),
                    DetectName = phiC >= ArkheInvariants.GHOST ? "Constitutional" : "Violation",
                    MD5String = GenerateSealHash(nodeId, invariantName, phiC)
                }
            };

            // Enviar para CrowdStrike
            using var request = new HttpRequestMessage(HttpMethod.Post, "ioa/entities/detections/v1");
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _accessToken);
            request.Content = JsonContent.Create(ioaEvent);
            var response = await _httpClient.SendAsync(request);

            response.EnsureSuccessStatusCode();

            // Disparar Real-time Response para remediação crítica
            if (violationType == "SealTampering" || violationType == "AutocideBreach")
            {
                await ExecuteRtrCommandAsync(nodeId, "contain");
            }

            return true;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"⚠️  CrowdStrike report failed: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Registra Custom IOA no CrowdStrike.
    /// </summary>
    public async Task<bool> RegisterIoARuleAsync(ConstitutionalDetectionRule rule)
    {
        await EnsureAccessTokenAsync();

        try
        {
            var ioaRule = new CrowdStrikeIoARule
            {
                Name = $"Arkhe-{rule.RuleName}",
                Description = rule.Description,
                PatternSeverity = MapToFalconSeverity(0, rule.RuleName),
                RuleType = "custom_ioa",
                PatternExpression = TranslateToFalconQuery(rule)
            };

            using var request = new HttpRequestMessage(HttpMethod.Post, "ioa/entities/custom-detections/v1");
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _accessToken);
            request.Content = JsonContent.Create(ioaRule);
            var response = await _httpClient.SendAsync(request);

            response.EnsureSuccessStatusCode();
            return true;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"⚠️  CrowdStrike IOA registration failed: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Executa comando Real-time Response para remediação.
    /// </summary>
    private async Task ExecuteRtrCommandAsync(string deviceId, string command)
    {
        using var request1 = new HttpRequestMessage(HttpMethod.Post, "real-time-response/combined/batch-init-session/v1");
        request1.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _accessToken);
        request1.Content = JsonContent.Create(new { DeviceIds = new[] { deviceId } });
        var rtrSession = await _httpClient.SendAsync(request1);

        rtrSession.EnsureSuccessStatusCode();

        var session = await rtrSession.Content.ReadFromJsonAsync<RtrSessionResponse>();

        using var request2 = new HttpRequestMessage(HttpMethod.Post, "real-time-response/combined/batch-command/v1");
        request2.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _accessToken);
        request2.Content = JsonContent.Create(
            new
            {
                SessionId = session.BatchId,
                BaseCommand = command,
                CommandString = command == "contain" ? "contain" : "runscript -CloudFile='arkhe_remediate'"
            });

        var response2 = await _httpClient.SendAsync(request2);
        response2.EnsureSuccessStatusCode();
    }

    private string MapToFalconSeverity(double phiC, string violationType)
    {
        if (violationType.Contains("Tampering") || violationType.Contains("Autocide")) return "Critical";
        if (phiC < ArkheInvariants.GHOST * 0.8) return "High";
        if (phiC < ArkheInvariants.GHOST) return "Medium";
        return "Low";
    }

    /// <summary>
    /// Traduz query KQL Arkhe para Falcon Query Language (FQL).
    /// </summary>
    private string TranslateToFalconQuery(ConstitutionalDetectionRule rule)
    {
        return rule.RuleName switch
        {
            "ConstitutionalViolation_Ghost" =>
                "EventType=ProcessRollup2 AND CommandLine Contains 'Arkhe' AND ContextBaseFileName Contains 'ArkheNode'",
            "ConstitutionalViolation_Loopseal" =>
                "EventType=ProcessRollup2 AND TargetProcessId_decimal > 0 AND CommandLine Contains 'seal'",
            "ConstitutionalViolation_Gap" =>
                "EventType=ProcessRollup2 AND CommandLine Contains 'Arkhe' AND ParentBaseFileName Contains 'Arkhe'",
            "PhiC_Critical_Degradation" =>
                "EventType=ProcessRollup2 AND CommandLine Contains 'Arkhe' AND TargetProcessId_decimal > 0",
            "Seal_Tampering_Detected" =>
                "EventType=RegKeySecurityDecrease AND RegObjectName Contains 'Arkhe'",
            "Autocide_Threshold_Breach" =>
                "EventType=ProcessRollup2 AND CommandLine Contains 'autocide'",
            "ETW_Provider_Disable_Attempt" =>
                "EventType=RegKeySecurityDecrease AND RegObjectName Contains 'ETW'",
            _ => $"EventType=ProcessRollup2 AND CommandLine Contains '{rule.RuleName.Replace("'", "\\'")}'"
        };
    }

    private string GenerateSealHash(string nodeId, string invariant, double phiC)
    {
        var payload = $"{nodeId}:{invariant}:{phiC:F4}:{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}";
        var hash = TemporalSealGenerator.SHA3_256(Encoding.UTF8.GetBytes(payload));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }
}

// Schemas CrowdStrike
public record FalconTokenResponse
{
    [JsonPropertyName("access_token")] public string AccessToken { get; init; }
    [JsonPropertyName("expires_in")] public int ExpiresIn { get; init; }
}
public record CrowdStrikeIoAEvent { public IoAEventDetail Event { get; init; } }
public record IoAEventDetail
{
    public string HostName { get; init; }
    public string PlatformName { get; init; }
    public string IOAName { get; init; }
    public string IOADescription { get; init; }
    public string Severity { get; init; }
    public string DetectName { get; init; }
    public string MD5String { get; init; }
}
public record CrowdStrikeIoARule
{
    public string Name { get; init; }
    public string Description { get; init; }
    public string PatternSeverity { get; init; }
    public string RuleType { get; init; }
    public string PatternExpression { get; init; }
}
public record RtrSessionResponse { [JsonPropertyName("batch_id")] public string BatchId { get; init; } }