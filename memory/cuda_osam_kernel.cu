// cuda_osam_kernel.cu — Substrato 199.7: CUDA Optimization for OSAM
// Canon: ∞.Ω.∇+++.199.7.cuda
// Objetivo: Reduzir overhead de inferência do δ‑mem para <5% via kernel CUDA otimizado

#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <math.h>
#include <stdio.h>
#include <vector>

// Configurações do kernel
#define OSAM_R 8                    // Dimensão do estado S ∈ ℝ^{r×r}
#define OSAM_MAX_STATES 4         // Número máximo de sub-estados (MSW)
#define BLOCK_SIZE 256            // Tamanho do bloco CUDA
#define WARP_SIZE 32              // Tamanho do warp NVIDIA

// Estrutura do estado OSAM em memória GPU
struct OSAMState {
    float S[OSAM_MAX_STATES][OSAM_R][OSAM_R];  // Estados S_i
    float beta_gate[OSAM_R];                    // Gate de escrita β
    float lambda_gate[OSAM_R];                  // Gate de esquecimento λ = 1-β
    int active_states;                          // Número de estados ativos
};

// Estrutura de projeções de memória
struct MemoryProjections {
    float q_m[OSAM_R];   // Query de memória
    float k_m[OSAM_R];   // Key de memória
    float v_m[OSAM_R];   // Value de memória
};

// ============================================================================
// KERNEL 1: Leitura do Estado OSAM (r_t = S_{t-1} · q^m)
// ============================================================================

__global__ void osam_read_kernel(
    const float* S,           // [num_states, r, r] estado em memória global
    const float* q_m,         // [r] query de memória
    float* r_t,               // [num_states * r] saída concatenada
    int r,                    // dimensão do estado
    int num_states            // número de estados ativos
) {
    int state_idx = blockIdx.x;
    int vec_idx = threadIdx.x;

    if (state_idx >= num_states || vec_idx >= r) return;

    // Cada thread computa um elemento do vetor de leitura r_t[state_idx][vec_idx]
    float sum = 0.0f;
    #pragma unroll
    for (int k = 0; k < r; ++k) {
        // S[state_idx][vec_idx][k] * q_m[k]
        int s_idx = ((state_idx * r + vec_idx) * r + k);
        sum += S[s_idx] * q_m[k];
    }

    // Escrever resultado: r_t[state_idx * r + vec_idx]
    int out_idx = state_idx * r + vec_idx;
    r_t[out_idx] = sum;
}

// ============================================================================
// KERNEL 2: Escrita Delta com Gates (S_t = λ ⊙ S + β ⊙ (v - S·k) ⊗ k^T)
// ============================================================================

__global__ void osam_write_delta_kernel(
    float* S,                 // [r, r] estado a atualizar (in-place)
    const float* k_m,         // [r] key de memória
    const float* v_m,         // [r] value de memória
    const float* beta,        // [r] gate de escrita
    const float* lambda,      // [r] gate de esquecimento
    int r                     // dimensão do estado
) {
    // Cada thread block processa uma linha da matriz S
    int row = blockIdx.x;
    int col = threadIdx.x;

    if (row >= r || col >= r) return;

    // Calcular predição: (S · k)[row]
    float pred = 0.0f;
    #pragma unroll
    for (int k = 0; k < r; ++k) {
        pred += S[row * r + k] * k_m[k];
    }

    // Residual: v[row] - pred
    float residual = v_m[row] - pred;

    // Atualização delta com gates element-wise:
    // S[row][col] = λ[row] * S[row][col] + β[col] * residual * k_m[col]
    float old_val = S[row * r + col];
    float new_val = lambda[row] * old_val + beta[col] * residual * k_m[col];

    S[row * r + col] = new_val;
}

// ============================================================================
// KERNEL 3: Correção de Atenção (Δq, Δo = W · r_t)
// ============================================================================

__global__ void attention_correction_kernel(
    const float* r_t,         // [r_read] vetor de leitura
    const float* W_delta_q,   // [d_head, r_read] pesos para Δq
    const float* W_delta_o,   // [d_head, r_read] pesos para Δo
    float* delta_q,           // [d_head] saída Δq
    float* delta_o,           // [d_head] saída Δo
    int r_read,               // dimensão de leitura (r ou r*num_states)
    int d_head,               // dimensão da cabeça de atenção
    float alpha_scale         // Fator de escala α / r_read
) {
    int head_idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (head_idx >= d_head) return;

    float dq_sum = 0.0f, do_sum = 0.0f;

    #pragma unroll
    for (int i = 0; i < r_read; ++i) {
        float r_val = r_t[i];
        dq_sum += W_delta_q[head_idx * r_read + i] * r_val;
        do_sum += W_delta_o[head_idx * r_read + i] * r_val;
    }

    // Aplicar fator de escala
    float scale = alpha_scale / r_read;
    delta_q[head_idx] = dq_sum * scale;
    delta_o[head_idx] = do_sum * scale;
}

// ============================================================================
// FUNÇÃO HOST: Orquestração dos Kernels CUDA
// ============================================================================

class CudaOSAMOptimizer {
public:
    CudaOSAMOptimizer(int r = 8, int num_states = 4, int d_head = 128)
        : r_(r), num_states_(num_states), d_head_(d_head), r_read_(r * num_states) {

        // Alocar memória GPU para estado OSAM
        cudaMalloc(&d_S_, num_states_ * r_ * r_ * sizeof(float));
        cudaMalloc(&d_projections_, 3 * r_ * sizeof(float));  // q_m, k_m, v_m
        cudaMalloc(&d_gates_, 2 * r_ * sizeof(float));         // beta, lambda
        cudaMalloc(&d_r_t_, r_read_ * sizeof(float));
        cudaMalloc(&d_delta_q_, d_head_ * sizeof(float));
        cudaMalloc(&d_delta_o_, d_head_ * sizeof(float));
        cudaMalloc(&d_W_delta_, 2 * d_head_ * r_read_ * sizeof(float));  // W_q + W_o

        // Inicializar estado com zeros
        cudaMemset(d_S_, 0, num_states_ * r_ * r_ * sizeof(float));

        // Configurar streams para paralelismo
        cudaStreamCreate(&stream_read_);
        cudaStreamCreate(&stream_write_);
        cudaStreamCreate(&stream_correct_);
    }

    ~CudaOSAMOptimizer() {
        cudaFree(d_S_);
        cudaFree(d_projections_);
        cudaFree(d_gates_);
        cudaFree(d_r_t_);
        cudaFree(d_delta_q_);
        cudaFree(d_delta_o_);
        cudaFree(d_W_delta_);
        cudaStreamDestroy(stream_read_);
        cudaStreamDestroy(stream_write_);
        cudaStreamDestroy(stream_correct_);
    }

    // Leitura: r_t = S · q_m (paralelo por estado)
    cudaError_t read(const float* h_q_m, float* h_r_t, int state_idx = -1) {
        // Copiar q_m para GPU
        cudaMemcpyAsync(d_projections_, h_q_m, r_ * sizeof(float),
                       cudaMemcpyHostToDevice, stream_read_);

        // Lançar kernel de leitura
        dim3 blocks(num_states_);
        dim3 threads(r_);
        osam_read_kernel<<<blocks, threads, 0, stream_read_>>>(
            d_S_, d_projections_, d_r_t_, r_, num_states_
        );

        // Copiar resultado de volta
        cudaMemcpyAsync(h_r_t, d_r_t_, r_read_ * sizeof(float),
                       cudaMemcpyDeviceToHost, stream_read_);

        return cudaStreamSynchronize(stream_read_);
    }

    // Escrita delta: S = λ ⊙ S + β ⊙ (v - S·k) ⊗ k^T
    cudaError_t write_delta(const float* h_k_m, const float* h_v_m,
                           const float* h_beta, const float* h_lambda,
                           int state_idx = 0) {
        // Copiar inputs para GPU
        float* d_k_m = d_projections_ + r_;
        float* d_v_m = d_projections_ + 2 * r_;
        float* d_beta = d_gates_;
        float* d_lambda = d_gates_ + r_;

        cudaMemcpyAsync(d_k_m, h_k_m, r_ * sizeof(float), cudaMemcpyHostToDevice, stream_write_);
        cudaMemcpyAsync(d_v_m, h_v_m, r_ * sizeof(float), cudaMemcpyHostToDevice, stream_write_);
        cudaMemcpyAsync(d_beta, h_beta, r_ * sizeof(float), cudaMemcpyHostToDevice, stream_write_);
        cudaMemcpyAsync(d_lambda, h_lambda, r_ * sizeof(float), cudaMemcpyHostToDevice, stream_write_);

        // Lançar kernel de escrita (apenas para estado especificado)
        float* d_S_state = d_S_ + state_idx * r_ * r_;
        dim3 blocks(r_);
        dim3 threads(r_);
        osam_write_delta_kernel<<<blocks, threads, 0, stream_write_>>>(
            d_S_state, d_k_m, d_v_m, d_beta, d_lambda, r_
        );

        return cudaStreamSynchronize(stream_write_);
    }

    // Correção de atenção: Δq, Δo = W · r_t
    cudaError_t compute_corrections(const float* h_r_t, float* h_delta_q, float* h_delta_o,
                                   const float* h_W_delta_q, const float* h_W_delta_o,
                                   float alpha = 16.0f) {
        // Copiar r_t e pesos para GPU
        cudaMemcpyAsync(d_r_t_, h_r_t, r_read_ * sizeof(float), cudaMemcpyHostToDevice, stream_correct_);
        cudaMemcpyAsync(d_W_delta_, h_W_delta_q, d_head_ * r_read_ * sizeof(float), cudaMemcpyHostToDevice, stream_correct_);
        cudaMemcpyAsync(d_W_delta_ + d_head_ * r_read_, h_W_delta_o, d_head_ * r_read_ * sizeof(float), cudaMemcpyHostToDevice, stream_correct_);

        // Lançar kernel de correção
        int threads_per_block = 256;
        int num_blocks = (d_head_ + threads_per_block - 1) / threads_per_block;
        float scale = alpha / r_read_;

        attention_correction_kernel<<<num_blocks, threads_per_block, 0, stream_correct_>>>(
            d_r_t_, d_W_delta_, d_W_delta_ + d_head_ * r_read_,
            d_delta_q_, d_delta_o_, r_read_, d_head_, scale
        );

        // Copiar resultados de volta
        cudaMemcpyAsync(h_delta_q, d_delta_q_, d_head_ * sizeof(float), cudaMemcpyDeviceToHost, stream_correct_);
        cudaMemcpyAsync(h_delta_o, d_delta_o_, d_head_ * sizeof(float), cudaMemcpyDeviceToHost, stream_correct_);

        return cudaStreamSynchronize(stream_correct_);
    }

    // Métricas de performance
    struct PerformanceMetrics {
        float read_latency_us;
        float write_latency_us;
        float correction_latency_us;
        float total_overhead_percent;
    };

    PerformanceMetrics measure_performance(int num_iterations = 100) {
        PerformanceMetrics metrics = {};
        cudaEvent_t start, stop;
        cudaEventCreate(&start);
        cudaEventCreate(&stop);

        // Medir leitura
        std::vector<float> h_q_m(r_, 0.5f), h_r_t(r_read_);
        cudaEventRecord(start, stream_read_);
        for (int i = 0; i < num_iterations; ++i) {
            read(h_q_m.data(), h_r_t.data());
        }
        cudaEventRecord(stop, stream_read_);
        cudaEventSynchronize(stop);
        float elapsed_ms;
        cudaEventElapsedTime(&elapsed_ms, start, stop);
        metrics.read_latency_us = (elapsed_ms * 1000) / num_iterations;

        // Medir escrita
        std::vector<float> h_k_m(r_, 0.3f), h_v_m(r_, 0.4f), h_beta(r_, 0.7f), h_lambda(r_, 0.3f);
        cudaEventRecord(start, stream_write_);
        for (int i = 0; i < num_iterations; ++i) {
            write_delta(h_k_m.data(), h_v_m.data(), h_beta.data(), h_lambda.data());
        }
        cudaEventRecord(stop, stream_write_);
        cudaEventSynchronize(stop);
        cudaEventElapsedTime(&elapsed_ms, start, stop);
        metrics.write_latency_us = (elapsed_ms * 1000) / num_iterations;

        // Medir correção
        std::vector<float> h_W_q(d_head_ * r_read_, 0.1f), h_W_o(d_head_ * r_read_, 0.1f);
        std::vector<float> h_delta_q(d_head_), h_delta_o(d_head_);
        cudaEventRecord(start, stream_correct_);
        for (int i = 0; i < num_iterations; ++i) {
            compute_corrections(h_r_t.data(), h_delta_q.data(), h_delta_o.data(),
                              h_W_q.data(), h_W_o.data());
        }
        cudaEventRecord(stop, stream_correct_);
        cudaEventSynchronize(stop);
        cudaEventElapsedTime(&elapsed_ms, start, stop);
        metrics.correction_latency_us = (elapsed_ms * 1000) / num_iterations;

        // Calcular overhead total vs baseline (estimado)
        float baseline_latency_us = 50.0f;  // Estimativa de latência baseline sem δ‑mem
        float delta_latency = metrics.read_latency_us + metrics.write_latency_us + metrics.correction_latency_us;
        metrics.total_overhead_percent = (delta_latency / baseline_latency_us) * 100;

        cudaEventDestroy(start);
        cudaEventDestroy(stop);
        return metrics;
    }

private:
    int r_, num_states_, d_head_, r_read_;
    float *d_S_, *d_projections_, *d_gates_, *d_r_t_, *d_delta_q_, *d_delta_o_, *d_W_delta_;
    cudaStream_t stream_read_, stream_write_, stream_correct_;
};