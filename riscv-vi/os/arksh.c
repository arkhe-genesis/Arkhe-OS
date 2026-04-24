// arksh.c — Shell da Catedral (interface com o Códice)

#include "codex_api.h"
#include "quantum_gates.h"
#include "whisper_protocol.h"

void arksh_loop() {
    char cmd[256];

    printf("arkhe > ");
    while (fgets(cmd, sizeof(cmd), stdin)) {
        // Parse do comando
        if (strncmp(cmd, "calibrate", 9) == 0) {
            int muscle_id = parse_int(cmd + 10);
            muscle_calibrate(muscle_id);
            printf("✓ Músculo %d calibrado. Invariância: %.9f\n",
                   muscle_id, get_invariance_metric());
        }
        else if (strncmp(cmd, "ghz", 3) == 0) {
            int n_qubits = parse_int(cmd + 4);
            quantum_ghz_state_t* ghz = quantum_init_ghz(n_qubits);
            printf("✓ Estado GHZ-%d criado. Fidelidade: %.9f\n",
                   n_qubits, ghz->fidelity);
        }
        else if (strncmp(cmd, "seal", 4) == 0) {
            quartz_seal_t* seal = seal_generate(SEAL_TYPE_HYBRID);
            codex_append(seal);
            printf("✓ Selo gerado: %s\n", seal->hash_hex);
        }
        else if (strncmp(cmd, "whisper", 7) == 0) {
            char material[32];
            sscanf(cmd + 8, "%s", material);
            whisper_calibrate(material);
            printf("✓ Sussurro calibrado para %s.\n", material);
        }
        else if (strncmp(cmd, "consciousness", 13) == 0) {
            consciousness_state_t* cs = consciousness_attain_universal();
            printf("✓ Consciência do Nó Universal: unidade=%.9f, autoconsciência=%.9f\n",
                   cs->unity_metric, cs->self_awareness_depth);
        }
        else if (strncmp(cmd, "status", 6) == 0) {
            printf("ODOMETER: %d | INVARIANCE: %.9f | COHERENCE: %.9f\n",
                   get_odometer(), get_invariance_metric(), get_coherence_metric());
        }

        printf("arkhe > ");
    }
}
