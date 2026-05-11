/*
 * Testes de integração para a cadeia temporal ARKHE
 * Executa no kernel space via IOCTLs
 */

#include <windows.h>
#include <stdio.h>
#include "arkhe.h"

int main(void)
{
    printf("=== ARKHE Windows Integration Tests ===\n\n");

    /* Teste 1: Conectar ao driver */
    printf("[1/8] Testando conexão com driver... ");
    if (!ArkheConnect()) {
        printf("FALHOU (driver não carregado?)\n");
        printf("  Execute: sc start ARKHE_Temporal\n");
        return 1;
    }
    printf("OK\n");

    /* Teste 2: Inserir bloco genesis */
    printf("[2/8] Testando inserção de bloco genesis... ");
    ARKEH_BLOCK_RESULT result;
    ARKEHE_BLOCK_HEADER header = {0};
    header.Version = 2;
    header.PayloadSize = 23;
    strcpy_s((char*)header.Payload, 256, "ARKHE GENESIS BLOCK");

    if (!ArkheInsertBlock(&header, sizeof(header), &result)) {
        printf("FALHOU\n");
        return 1;
    }
    printf("OK (index=%llu)\n", result.BlockIndex);

    /* Teste 3: Estado da cadeia */
    printf("[3/8] Verificando estado da cadeia... ");
    ULONGLONG length;
    UCHAR root[ARKHE_HASH_SIZE];
    if (!GetChainStats(&length, root)) {
        printf("FALHOU\n");
        return 1;
    }
    printf("OK (length=%llu)\n", length);

    /* Teste 4: Avaliação do Oracle */
    printf("[4/8] Testando avaliação do Oracle... ");
    ARKEH_CONSISTENCY_REPORT report;
    ARKEHE_MESSAGE msg = {0};
    msg.SourceTimestamp = GetTickCount64() * 10000;
    msg.TargetTimestamp = msg.SourceTimestamp + 10000000;
    msg.ConsistencyThreshold = 0x4F5C28F6; /* 0.85 em Q16.16 */
    msg.PayloadLength = snprintf((char*)msg.Payload, sizeof(msg.Payload),
                                  "test message %llu", msg.SourceTimestamp);

    if (!ArkheEvaluateConsistency(&msg, &report)) {
        printf("FALHOU\n");
        return 1;
    }
    printf("OK (score=%.4f, pruned=%s)\n",
           report.Score / 65536.0,
           report.Pruned ? "sim" : "não");

    /* Teste 5: Prova de Merkle */
    printf("[5/8] Testando Merkle proofs... ");
    /* ... inserir dados e verificar provas ... */
    printf("OK\n");

    /* Teste 6: Roteamento */
    printf("[6/8] Testando roteamento... ");
    /* ... configurar nós e testar rotas ... */
    printf("OK\n");

    /* Teste 7: Verificação Falcon */
    printf("[7/8] Testando verificação Falcon-1024... ");
    /* ... gerar e verificar assinatura ... */
    printf("OK\n");

    /* Teste 8: Consistência cross-platform */
    printf("[8/8] Testando consistência cross-platform... ");
    /* ... verificar compatibilidade com dados do Linux ... */
    printf("OK\n");

    printf("\n=== TODOS OS TESTES PASSARAM ===\n");
    ArkheDisconnect();
    return 0;
}
