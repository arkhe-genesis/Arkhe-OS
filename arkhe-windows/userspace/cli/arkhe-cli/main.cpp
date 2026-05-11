/*
 * ARKHE Ω-TEMP — Command Line Interface
 *
 * Ferramenta CLI para interagir com o ARKHE OS.
 * Suporta comandos de roteamento, consenso, ledger e provas ZK.
 */

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../libarkhe/include/arkhe.h"

/*
 * Comandos disponíveis
 */
typedef enum {
    CMD_ROUTE,
    CMD_CONSENSUS,
    CMD_LEDGER,
    CMD_BLOCK,
    CMD_STATUS,
    CMD_ZKPROVE,
    CMD_ZKVERIFY,
    CMD_SOLAR,
    CMD_HELP,
    CMD_EXIT
} Command;

/*
 * Parser de argumentos
 */
Command ParseCommand(const char* cmd)
{
    if (_stricmp(cmd, "route") == 0) return CMD_ROUTE;
    if (_stricmp(cmd, "consensus") == 0) return CMD_CONSENSUS;
    if (_stricmp(cmd, "ledger") == 0) return CMD_LEDGER;
    if (_stricmp(cmd, "block") == 0) return CMD_BLOCK;
    if (_stricmp(cmd, "status") == 0) return CMD_STATUS;
    if (_stricmp(cmd, "zkprove") == 0) return CMD_ZKPROVE;
    if (_stricmp(cmd, "zkverify") == 0) return CMD_ZKVERIFY;
    if (_stricmp(cmd, "solar") == 0) return CMD_SOLAR;
    if (_stricmp(cmd, "help") == 0) return CMD_HELP;
    if (_stricmp(cmd, "exit") == 0) return CMD_EXIT;
    return CMD_HELP;
}

/*
 * Executar comando
 */
BOOL ExecuteCommand(Command cmd, int argc, char** argv)
{
    switch (cmd) {
        case CMD_ROUTE:
            return ExecuteRouteCommand(argc, argv);
        case CMD_CONSENSUS:
            return ExecuteConsensusCommand(argc, argv);
        case CMD_LEDGER:
            return ExecuteLedgerCommand(argc, argv);
        case CMD_BLOCK:
            return ExecuteBlockCommand(argc, argv);
        case CMD_STATUS:
            return ExecuteStatusCommand();
        case CMD_ZKPROVE:
            return ExecuteZKProveCommand(argc, argv);
        case CMD_ZKVERIFY:
            return ExecuteZKVerifyCommand(argc, argv);
        case CMD_SOLAR:
            return ExecuteSolarCommand();
        case CMD_HELP:
            PrintHelp();
            return TRUE;
        case CMD_EXIT:
            return FALSE;
        default:
            return FALSE;
    }
}

/*
 * Comando: route — Encontrar melhor rota
 */
BOOL ExecuteRouteCommand(int argc, char** argv)
{
    if (argc < 4) {
        fprintf(stderr, "Uso: arkhe route <origem> <destino> [--optimize]\n");
        return FALSE;
    }

    const char* source = argv[2];
    const char* dest = argv[3];
    BOOLEAN optimize = (argc > 4 && strcmp(argv[4], "--optimize") == 0);

    printf("ARKHE Route: %s → %s\n", source, dest);
    printf("Consultando roteador temporal...\n");

    /* Chamar driver para encontrar rota */
    ARKEH_ROUTE_RESULT result;
    if (!ArkheFindRoute(source, dest, optimize, &result)) {
        fprintf(stderr, "Rota não encontrada\n");
        return FALSE;
    }

    printf("Rota encontrada (%d hops):\n", result.HopCount);
    for (ULONG i = 0; i < result.HopCount; i++) {
        printf("  [%lu] %s (custo: %.4f, consenso: %.2f%%)\n",
               i + 1,
               result.Hops[i].Name,
               result.Hops[i].TotalCost,
               result.Hops[i].ConsensusScore * 100.0);
    }
    printf("Custo total: %.4f\n", result.TotalCost);
    printf("Consenso mínimo: %.2f%%\n",
           result.MinConsensus * 100.0);

    return TRUE;
}

/*
 * Comando: consensus — Avaliar consistência
 */
BOOL ExecuteConsensusCommand(int argc, char** argv)
{
    printf("=== ARKHE Consenso Oracle ===\n");
    printf("Status: ");

    ARKEH_ORACLE_STATS stats;
    if (ArkheGetOracleStats(&stats)) {
        printf("OPERACIONAL\n");
        printf("  Avaliações: %llu\n", stats.TotalEvaluations);
        printf("  Podados: %llu (%.2f%%)\n",
               stats.Pruned,
               stats.PruningRate * 100.0);
        printf("  Paradoxos: %llu\n", stats.ParadoxCount);
        printf("  Score médio: %.4f\n", stats.AvgScore);
    } else {
        printf("NÃO DISPONÍVEL\n");
    }

    return TRUE;
}

/*
 * Comando: status — Status geral do sistema
 */
BOOL ExecuteStatusCommand(VOID)
{
    printf("╔══════════════════════════════════════════════════╗\n");
    printf("║           ARKHE Ω-TEMP STATUS                    ║\n");
    printf("╠══════════════════════════════════════════════════╣\n");

    /* Driver */
    printf("║ Driver:    ");
    if (ArkheIsDriverLoaded()) {
        printf("✓ CARREGADO                        ║\n");
    } else {
        printf("✗ NÃO CARREGADO                     ║\n");
    }

    /* Chain temporal */
    printf("║ Chain:     ");
    ULONGLONG length = ArkheGetChainLength();
    printf("✓ %llu blocos                              ║\n", length);

    /* Oracle */
    printf("║ Oracle:    ");
    if (ArkheOracleIsRunning()) {
        printf("✓ ATIVO                              ║\n");
    } else {
        printf("✗ INATIVO                            ║\n");
    }

    /* Router */
    printf("║ Router:    ");
    if (ArkheRouterIsRunning()) {
        printf("✓ ATIVO                              ║\n");
    } else {
        printf("✗ INATIVO                            ║\n");
    }

    /* Merkle */
    printf("║ Merkle:    ");
    printf("✓ %lu nós indexados                    ║\n",
           ArkheGetMerkleLeafCount());

    printf("╚══════════════════════════════════════════════════╝\n");

    return TRUE;
}
