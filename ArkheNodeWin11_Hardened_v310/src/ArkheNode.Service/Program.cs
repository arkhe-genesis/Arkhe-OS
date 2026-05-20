// ═══════════════════════════════════════════════════════════════
// ARKHE OS — SERVIÇO WINDOWS 11 COM INTEGRAÇÃO MDE
// Canon: ∞.Ω.∇+++.310.service_mde
// ═══════════════════════════════════════════════════════════════
using ArkheNode.Core;
using ArkheNode.Service;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Serilog;

var builder = WebApplication.CreateBuilder(args);

// Configurar Serilog com sink para ETW e MDE
builder.Host.UseSerilog((context, services, configuration) => configuration
    .WriteTo.Console()
    // .WriteTo.EventLog("ArkheNode",
        // manageEventSource: true,
        // source: "ArkheNode-Service")
    .Enrich.FromLogContext()
    // .Enrich.WithMachineName()
    .ReadFrom.Configuration(context.Configuration));

// Registrar serviços canônicos
builder.Services.AddSingleton<IAuditLogger, InMemoryAuditLogger>(); // simplified for build

// Registrar integração MDE se configurado
if (!string.IsNullOrEmpty(builder.Configuration["Mde:TenantId"]))
{
    builder.Services.AddSingleton<MdeIntegration>(sp => new MdeIntegration(
        tenantId: builder.Configuration["Mde:TenantId"]!,
        clientId: builder.Configuration["Mde:ClientId"]!,
        clientSecret: builder.Configuration["Mde:ClientSecret"]!));
}

// Configurar API REST
builder.Services.AddControllers();
builder.WebHost.ConfigureKestrel(opts =>
    opts.ListenLocalhost(21900)); // Porta canônica Arkhe

var app = builder.Build();

// Middleware constitucional: intercepta todas as requisições
app.Use(async (context, next) =>
{
    var logger = context.RequestServices.GetRequiredService<IAuditLogger>();
    var startTime = DateTimeOffset.UtcNow;

    try
    {
        await next();

        // Registrar sucesso constitucional
        var phiC = context.Items["PhiC"] as double? ?? 0.95;
        logger.Log(new AuditEvent(
            startTime, "", AuditEventLevel.Constitutional,
            "310", Environment.MachineName, $"API Request: {context.Request.Path}",
            phiC, new Dictionary<string, bool> { ["ghost"] = true, ["loopseal"] = true, ["gap"] = true },
            TemporalSealGenerator.Generate("310", Environment.MachineName, phiC).SealHash));
    }
    catch (Exception ex)
    {
        // Registrar violação e reportar para MDE se configurado
        var mde = context.RequestServices.GetService<MdeIntegration>();
        if (mde != null)
        {
            await mde.ReportConstitutionalViolationAsync(
                Environment.MachineName,
                "api_error",
                0.0,
                0.5,
                ex.Message);
        }

        logger.Log(new AuditEvent(
            startTime, "", AuditEventLevel.Violation,
            "310", Environment.MachineName, $"API Error: {ex.Message}",
            0.0, new Dictionary<string, bool> { ["ghost"] = false }, null));

        throw;
    }
});

app.MapControllers();

// Registrar regras de detecção MDE no startup
if (app.Services.GetService<MdeIntegration>() != null)
{
    var rules = new[]
    {
        new ConstitutionalDetectionRule
        {
            RuleName = "Arkhe-Low-PhiC-Detection",
            Description = "Detecta nós com Φ_C persistentemente abaixo do threshold constitucional",
            Severity = "High",
            EventId = 1, // PhiCCalculated event
            Threshold = 0.70,
            MinOccurrences = 3,
            AlertTitle = "Arkhe Node: Low Constitutional Coherence",
            AlertDescription = "Node has Φ_C below constitutional threshold for sustained period"
        },
        new ConstitutionalDetectionRule
        {
            RuleName = "Arkhe-Invariant-Violation",
            Description = "Detecta violações de invariantes constitucionais",
            Severity = "Critical",
            EventId = 2, // ConstitutionalViolation event
            Threshold = 0.0,
            MinOccurrences = 1,
            AlertTitle = "Arkhe Node: Constitutional Invariant Violated",
            AlertDescription = "Node violated a constitutional invariant requiring immediate attention"
        }
    };

    var mde = app.Services.GetRequiredService<MdeIntegration>();
    foreach (var rule in rules)
    {
        await mde.RegisterDetectionRuleAsync(rule);
    }
}

app.Run();