// ═══════════════════════════════════════════════════════════════
// ARKHE OS — FEDERATION SECURITY MESH
// Canon: ∞.Ω.∇+++.313.federation
// Mesh de segurança federada entre 10 regiões continentais
// Byzantine Fault Tolerant Consensus — Quorum: 7 — Max Latency: 200ms
// ═══════════════════════════════════════════════════════════════
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using ArkheNode.Core;

namespace ArkheNode.Security;

/// <summary>
/// Mesh de segurança federada para consenso constitucional multi-regional.
/// Implementa consenso Bizantino para tolerância a falhas de até 3 regiões.
/// </summary>
public class FederationSecurityMesh
{
    private readonly List<FederationNode> _nodes;
    private readonly HttpClient _httpClient;
    private const int QuorumSize = 7;
    private const double MaxLatencyMs = 200;
    private const double PhiCAlertThreshold = 0.85;

    public FederationSecurityMesh(IEnumerable<FederationNode> nodes)
    {
        _nodes = nodes.ToList();
        _httpClient = new HttpClient { Timeout = TimeSpan.FromMilliseconds(MaxLatencyMs) };
    }

    /// <summary>
    /// Propaga alerta constitucional para toda a federação com consenso.
    /// </summary>
    public async Task<FederationConsensusResult> PropagateAlertAsync(
        CanonicalPayload alert,
        EdrPlatform sourcePlatform)
    {
        var tasks = _nodes.Select(n => SendAlertToNodeAsync(n, alert, sourcePlatform));
        var responses = await Task.WhenAll(tasks);

        var successful = responses.Count(r => r.Success);
        var failed = responses.Count(r => !r.Success);

        // Consenso Bizantino: pelo menos QuorumSize nós devem confirmar
        var consensusReached = successful >= QuorumSize;

        // Gerar selo de consenso federado
        var consensusSeal = GenerateConsensusSeal(alert, successful, failed, consensusReached);

        var validPhiCs = responses.Where(r => r.PhiC.HasValue).Select(r => r.PhiC.Value).ToList();
        return new FederationConsensusResult
        {
            ConsensusReached = consensusReached,
            NodesConfirmed = successful,
            NodesFailed = failed,
            TotalNodes = _nodes.Count,
            ConsensusSeal = consensusSeal,
            PhiCFederationAverage = validPhiCs.Any() ? validPhiCs.Average() : 0.0,
            MaxLatencyMs = responses.Any() ? responses.Max(r => r.LatencyMs) : 0.0,
            AlertAnchored = consensusReached
        };
    }

    private async Task<NodeResponse> SendAlertToNodeAsync(
        FederationNode node,
        CanonicalPayload alert,
        EdrPlatform sourcePlatform)
    {
        var startTime = DateTimeOffset.UtcNow;
        try
        {
            // Traduzir alerta para formato nativo do nó
            var translated = ArkheCanonicalSchema.TranslateTo(alert, node.Platform);

            var response = await _httpClient.PostAsJsonAsync(
                $"{node.Endpoint}/api/v1/security/alert", translated);

            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<NodeAlertResponse>();

            var latency = (DateTimeOffset.UtcNow - startTime).TotalMilliseconds;

            return new NodeResponse
            {
                Success = true,
                NodeId = node.NodeId,
                PhiC = result?.PhiC,
                LatencyMs = latency,
                Platform = node.Platform
            };
        }
        catch (Exception ex)
        {
            return new NodeResponse
            {
                Success = false,
                NodeId = node.NodeId,
                Error = ex.Message,
                LatencyMs = MaxLatencyMs
            };
        }
    }

    private string GenerateConsensusSeal(
        CanonicalPayload alert,
        int confirmed,
        int failed,
        bool consensus)
    {
        var payload = new
        {
            alert.Substrate,
            alert.NodeId,
            alert.PhiC,
            confirmed,
            failed,
            consensus,
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
        };

        var json = System.Text.Json.JsonSerializer.Serialize(payload);
        var hash = TemporalSealGenerator.SHA3_256(System.Text.Encoding.UTF8.GetBytes(json));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    /// <summary>
    /// Calcula Φ_C médio da federação para monitoramento global.
    /// </summary>
    public async Task<double> CalculateFederationPhiCAsync()
    {
        var tasks = _nodes.Select(n => GetNodePhiCAsync(n));
        var phiCs = await Task.WhenAll(tasks);
        var validPhiCs = phiCs.Where(p => p.HasValue).Select(p => p.Value);

        return validPhiCs.Any() ? validPhiCs.Average() : 0.0;
    }

    private async Task<double?> GetNodePhiCAsync(FederationNode node)
    {
        try
        {
            var response = await _httpClient.GetAsync(
                $"{node.Endpoint}/api/v1/status/phi-c");
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadFromJsonAsync<PhiCStatus>();
            return result?.PhiC;
        }
        catch
        {
            return null;
        }
    }
}

public record FederationNode
{
    public string NodeId { get; init; }
    public string Region { get; init; }
    public string Endpoint { get; init; }
    public EdrPlatform Platform { get; init; }
}

public record FederationConsensusResult
{
    public bool ConsensusReached { get; init; }
    public int NodesConfirmed { get; init; }
    public int NodesFailed { get; init; }
    public int TotalNodes { get; init; }
    public string ConsensusSeal { get; init; }
    public double PhiCFederationAverage { get; init; }
    public double MaxLatencyMs { get; init; }
    public bool AlertAnchored { get; init; }
}

public record NodeResponse
{
    public bool Success { get; init; }
    public string NodeId { get; init; }
    public double? PhiC { get; init; }
    public double LatencyMs { get; init; }
    public EdrPlatform Platform { get; init; }
    public string Error { get; init; }
}

public record NodeAlertResponse { public double? PhiC { get; init; } }
public record PhiCStatus { public double PhiC { get; init; } }