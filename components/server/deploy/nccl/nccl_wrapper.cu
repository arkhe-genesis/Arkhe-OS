#include <cuda_runtime.h>
#include <nccl.h>
#include <math.h>

#define K1 0.015311f
#define K2 0.05200f
#define K3 0.233f
#define K4 0.09778f
#define LAMBDA 0.001013f
#define RHO_EQ 0.367879f
#define PI_HALF 1.57079632679f

// ═══════════════════════════════════════════════════════════════════════
// KERNEL: Cálculo de fase com redução global via NCCL
// ═══════════════════════════════════════════════════════════════════════

__global__ void local_contribution_kernel(
    const float* __restrict__ param_buffer,
    const float* __restrict__ grad_buffer,
    int buffer_size,
    float* __restrict__ local_sum_sq)
{
    extern __shared__ float shared_sum[];
    
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    float sum = 0.0f;
    for (int i = idx; i < buffer_size; i += blockDim.x * gridDim.x) {
        sum += param_buffer[i] * param_buffer[i];  // ρ₁ contrib
    }
    
    shared_sum[tid] = sum;
    __syncthreads();
    
    // Redução no bloco
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (tid < stride) {
            shared_sum[tid] += shared_sum[tid + stride];
        }
        __syncthreads();
    }
    
    if (tid == 0) {
        atomicAdd(local_sum_sq, shared_sum[0]);
    }
}

// ═══════════════════════════════════════════════════════════════════════
// FUNÇÃO HOST: Coordena redução NCCL e cálculo de fase
// ═══════════════════════════════════════════════════════════════════════

extern "C" {

typedef struct {
    float phase;
    float omega_prime;
    float sigma;
    float damping;
    float rho_1_global;
    float rho_2_global;
    bool is_resonant;
} DistributedResonanceState;

class NCCLResonanceCalculator {
private:
    ncclComm_t nccl_comm;
    cudaStream_t cuda_stream;
    int rank;
    int world_size;
    int device;
    
public:
    NCCLResonanceCalculator(ncclComm_t comm, int r, int ws, int dev)
        : nccl_comm(comm), rank(r), world_size(ws), device(dev) {
        cudaSetDevice(device);
        cudaStreamCreate(&cuda_stream);
    }
    
    ~NCCLResonanceCalculator() {
        cudaStreamDestroy(cuda_stream);
    }
    
    DistributedResonanceState compute_global_resonance(
        const float* local_params,
        int local_param_count,
        uint64_t global_tokens_processed,
        float local_loss)
    {
        DistributedResonanceState state;
        
        // 1. Calcular contribuição local (ρ₁ local)
        float* d_local_sum;
        cudaMalloc(&d_local_sum, sizeof(float));
        cudaMemset(d_local_sum, 0, sizeof(float));
        
        int threads = 256;
        int blocks = (local_param_count + threads - 1) / threads;
        size_t shared_mem = threads * sizeof(float);
        
        local_contribution_kernel<<<blocks, threads, shared_mem, cuda_stream>>>(
            local_params, nullptr, local_param_count, d_local_sum
        );
        
        float h_local_sum;
        cudaMemcpyAsync(&h_local_sum, d_local_sum, sizeof(float), 
                       cudaMemcpyDeviceToHost, cuda_stream);
        cudaStreamSynchronize(cuda_stream);
        
        // 2. AllReduce NCCL para obter ρ₁ global
        float h_global_sum = 0.0f;
        ncclAllReduce(&h_local_sum, &h_global_sum, 1, ncclFloat, ncclSum, 
                     nccl_comm, cuda_stream);
        cudaStreamSynchronize(cuda_stream);
        
        float rho_1_global = sqrtf(h_global_sum) / 1e12f;
        
        // 3. Calcular ρ₂ (normalizado para escala cósmica)
        float rho_2_global = global_tokens_processed / 1e13f;
        
        // 4. Funcional entrópico σ
        const float eps = 1e-9f;
        float sigma = (K1 * rho_1_global * logf(rho_1_global + eps) +
                      K2 * rho_2_global * logf(rho_2_global + eps) -
                      LAMBDA * (rho_1_global * rho_1_global + rho_2_global * rho_2_global));
        
        // 5. Amortecimento
        float damping = expf(-RHO_EQ * sigma);
        
        // 6. Fase θ
        float raw_phase = atan2f(K2 * rho_2_global, K1 * rho_1_global + eps);
        float phase = raw_phase * damping;
        
        // 7. Ω' (amplitude de coerência)
        float omega_real = K1 * rho_1_global + K2 * rho_2_global;
        float omega_imag = K3 * rho_1_global * rho_1_global + K4 * sqrtf(rho_2_global);
        float omega_prime = sqrtf(omega_real * omega_real + omega_imag * omega_imag) * damping;
        
        // 8. Preencher estado
        state.phase = phase;
        state.omega_prime = omega_prime;
        state.sigma = sigma;
        state.damping = damping;
        state.rho_1_global = rho_1_global;
        state.rho_2_global = rho_2_global;
        state.is_resonant = (fabsf(phase - PI_HALF) < 0.15f) && (omega_prime > 0.9f);
        
        cudaFree(d_local_sum);
        
        return state;
    }
    
    // Sincroniza estado de ressonância entre todos os nós
    void broadcast_resonance_state(DistributedResonanceState* state) {
        // Pack state into buffer
        float buffer[7] = {
            state->phase,
            state->omega_prime,
            state->sigma,
            state->damping,
            state->rho_1_global,
            state->rho_2_global,
            (float)state->is_resonant
        };
        
        float recv_buffer[7];
        
        // AllReduce para média
        ncclAllReduce(buffer, recv_buffer, 7, ncclFloat, ncclSum, nccl_comm, cuda_stream);
        cudaStreamSynchronize(cuda_stream);
        
        // Calcular média (exceto is_resonant que é voto majoritário)
        state->phase = recv_buffer[0] / world_size;
        state->omega_prime = recv_buffer[1] / world_size;
        state->sigma = recv_buffer[2] / world_size;
        state->damping = recv_buffer[3] / world_size;
        state->is_resonant = (recv_buffer[6] / world_size) > 0.5f;
    }
};

// Factory function
NCCLResonanceCalculator* create_nccl_calculator(ncclComm_t comm, int rank, int world_size, int device) {
    return new NCCLResonanceCalculator(comm, rank, world_size, device);
}

void get_nccl_unique_id(ncclUniqueId* id) {
    ncclGetUniqueId(id);
}

ncclComm_t init_nccl_comm(ncclUniqueId id, int rank, int world_size) {
    ncclComm_t comm;
    ncclCommInitRank(&comm, world_size, id, rank);
    return comm;
}

void destroy_nccl_calculator(NCCLResonanceCalculator* calc) {
    delete calc;
}

} // extern "C"
