// ebpf_integrity.circom
// Verifica integridade de sequência de syscalls sem revelar detalhes sensíveis

pragma circom 2.1.6;

include "circomlib/poseidon.circom";
include "circomlib/comparators.circom";
include "circomlib/bitify.circom";

// Constantes de configuração
const SYSCALL_BATCH_SIZE = 1024;    // Número de syscalls por prova
const MAX_PID = 2**32 - 1;
const ENTROPY_THRESHOLD = 1000;     // Threshold de entropia mínima (anti-replay)

// Estrutura de um syscall (simplificada)
// signal timestamp;      // Timestamp do evento
// signal syscall_nr;     // Número da syscall (ex: 59 = execve)
// signal pid;            // Process ID
// signal uid;            // User ID
// signal retcode;        // Código de retorno
// signal hash_args;      // Hash dos argumentos (para privacidade)

// Template principal de verificação de integridade eBPF
template EBPFIntegrityVerifier(batch_size) {
    // Inputs privados (witness)
    signal input private syscalls[batch_size][6];  // Array de syscalls
    
    // Inputs públicos
    signal input public policy_hash;           // Hash da política de segurança
    signal input public entropy_threshold;     // Threshold configurável
    signal input public merkle_root_previous;  // Root anterior para continuidade
    signal input public timestamp_batch;       // Timestamp do batch
    
    // Outputs públicos
    signal output integrity_score;             // 0-10000 (pontuação de integridade)
    signal output nullifier;                   // Previne replay de batches
    signal output next_merkle_root;            // Para cadeia de provas
    
    // 1. Verificação de sequência temporal (anti-tampering)
    component time_checks[batch_size - 1];
    for (var i = 0; i < batch_size - 1; i++) {
        time_checks[i] = GreaterThan(64);
        time_checks[i].in[0] <== syscalls[i+1][0];  // timestamp[i+1]
        time_checks[i].in[1] <== syscalls[i][0];    // timestamp[i]
        // Cada syscall deve ter timestamp > anterior
        time_checks[i].out === 1;
    }
    
    // 2. Cálculo de entropia de Shannon dos PIDs (detecção de fork bombs)
    // Simplificação para circuito: usamos variância como proxy de entropia
    signal pid_mean;
    signal variance_sum;
    
    // Calcula média
    signal pid_sum;
    for (var i = 0; i < batch_size; i++) {
        pid_sum <== pid_sum + syscalls[i][2];
    }
    pid_mean <== pid_sum / batch_size;
    
    // Calcula variância
    for (var i = 0; i < batch_size; i++) {
        signal diff <== syscalls[i][2] - pid_mean;
        variance_sum <== variance_sum + diff * diff;
    }
    
    signal variance <== variance_sum / batch_size;
    
    // Verifica entropia suficiente (anti-patterns de ataque)
    component entropy_check = GreaterThan(32);
    entropy_check.in[0] <== variance;
    entropy_check.in[1] <== entropy_threshold;
    
    // 3. Detecção de syscalls proibidas (ex: ptrace, process_vm_writev)
    signal syscall_violations[batch_size];
    component is_ptrace[batch_size];
    component is_vmwrite[batch_size];
    
    for (var i = 0; i < batch_size; i++) {
        // Lista de syscalls perigosas: 101 (ptrace), 310 (process_vm_writev), etc.
        is_ptrace[i] = IsEqual();
        is_ptrace[i].in[0] <== syscalls[i][1];
        is_ptrace[i].in[1] <== 101;
        
        is_vmwrite[i] = IsEqual();
        is_vmwrite[i].in[0] <== syscalls[i][1];
        is_vmwrite[i].in[1] <== 310;
        
        // OR lógico: violação se qualquer uma for verdadeira
        syscall_violations[i] <== is_ptrace[i].out + is_vmwrite[i].out 
                                  - is_ptrace[i].out * is_vmwrite[i].out;
    }
    
    // Soma total de violações deve ser 0
    signal total_violations;
    for (var i = 0; i < batch_size; i++) {
        total_violations <== total_violations + syscall_violations[i];
    }
    total_violations === 0;
    
    // 4. Cálculo de hash acumulado (Merkle tree incremental)
    component poseidon_chain[batch_size];
    signal current_hash;
    
    // Inicializa com root anterior
    current_hash <== merkle_root_previous;
    
    for (var i = 0; i < batch_size; i++) {
        poseidon_chain[i] = Poseidon(7);
        poseidon_chain[i].inputs[0] <== current_hash;
        poseidon_chain[i].inputs[1] <== syscalls[i][0];  // timestamp
        poseidon_chain[i].inputs[2] <== syscalls[i][1];  // syscall_nr
        poseidon_chain[i].inputs[3] <== syscalls[i][2];  // pid
        poseidon_chain[i].inputs[4] <== syscalls[i][3];  // uid
        poseidon_chain[i].inputs[5] <== syscalls[i][4];  // retcode
        poseidon_chain[i].inputs[6] <== syscalls[i][5];  // hash_args
        
        current_hash <== poseidon_chain[i].out;
    }
    
    next_merkle_root <== current_hash;
    
    // 5. Cálculo de score de integridade (0-10000)
    // Baseado em: sequência válida (25%), entropia (25%), zero violações (50%)
    signal seq_valid_score <== 2500;  // Se chegou aqui, sequência é válida
    signal entropy_score <== entropy_check.out * 2500;
    
    component violations_gt_zero = GreaterThan(32);
    violations_gt_zero.in[0] <== total_violations;
    violations_gt_zero.in[1] <== 0;
    
    signal violation_score <== (1 - violations_gt_zero.out) * 5000;
    
    integrity_score <== seq_valid_score + entropy_score + violation_score;
    
    // 6. Geração de nullifier único
    component nullifier_hash = Poseidon(3);
    nullifier_hash.inputs[0] <== policy_hash;
    nullifier_hash.inputs[1] <== timestamp_batch;
    nullifier_hash.inputs[2] <== merkle_root_previous;
    
    nullifier <== nullifier_hash.out;
}

// Instanciação para batches de 1024 syscalls
component main {public [policy_hash, entropy_threshold, merkle_root_previous, timestamp_batch]} 
    = EBPFIntegrityVerifier(1024);
