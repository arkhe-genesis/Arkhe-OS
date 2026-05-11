import torch
import torch.distributed as dist
from typing import Optional, Dict, Any
import ctypes
import os

class NCCLResonanceWrapper:
    """
    Wrapper Python para sincronização NCCL de ressonância distribuída.
    """
    
    def __init__(self):
        self._lib = None
        self._calculator = None
        self._initialized = False
        
    def initialize(self, rank: int, world_size: int, device: int):
        """
        Inicializa o wrapper NCCL.
        Deve ser chamado após dist.init_process_group().
        """
        if not dist.is_initialized():
            raise RuntimeError("torch.distributed not initialized")
        
        # Carregar biblioteca compilada
        lib_path = os.path.join(os.path.dirname(__file__), 'libnccl_resonance.so')
        self._lib = ctypes.CDLL(lib_path)
        
        # Configurar tipos
        self._lib.create_nccl_calculator.restype = ctypes.c_void_p
        self._lib.create_nccl_calculator.argtypes = [
            ctypes.c_void_p,  # ncclComm_t
            ctypes.c_int,     # rank
            ctypes.c_int,     # world_size
            ctypes.c_int      # device
        ]
        
        self._lib.get_nccl_unique_id.argtypes = [ctypes.c_void_p]
        self._lib.init_nccl_comm.restype = ctypes.c_void_p
        self._lib.init_nccl_comm.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        
        # Obter NCCL communicator
        nccl_comm = self._get_nccl_comm(rank, world_size, device)
        
        self._calculator = self._lib.create_nccl_calculator(
            nccl_comm, rank, world_size, device
        )
        self._initialized = True
        
    def _get_nccl_comm(self, rank: int, world_size: int, device: int):
        """
        Cria um novo NCCL communicator coordenado via PyTorch dist.
        """
        # ncclUniqueId is 128 bytes
        unique_id = bytearray(128)
        
        if rank == 0:
            id_buffer = (ctypes.c_char * 128).from_buffer(unique_id)
            self._lib.get_nccl_unique_id(id_buffer)
            
        # Broadcast the unique ID from rank 0 to all other ranks
        id_tensor = torch.ByteTensor(list(unique_id)).to(f'cuda:{device}')
        dist.broadcast(id_tensor, src=0)
        
        unique_id_bytes = bytes(id_tensor.cpu().tolist())
        id_buffer = (ctypes.c_char * 128).from_buffer_copy(unique_id_bytes)
        
        return self._lib.init_nccl_comm(id_buffer, rank, world_size)
    
    def compute_global_resonance(
        self,
        local_params: torch.Tensor,
        global_tokens: int,
        local_loss: float
    ) -> Dict[str, Any]:
        """
        Computa estado de ressonância global com sincronização NCCL.
        """
        if not self._initialized:
            raise RuntimeError("NCCL wrapper not initialized")
        
        # Chamar kernel CUDA
        result = self._lib.compute_global_resonance(
            self._calculator,
            local_params.data_ptr(),
            local_params.numel(),
            global_tokens,
            local_loss
        )
        
        return {
            "phase": result.phase,
            "omega_prime": result.omega_prime,
            "sigma": result.sigma,
            "damping": result.damping,
            "rho_1_global": result.rho_1_global,
            "rho_2_global": result.rho_2_global,
            "is_resonant": bool(result.is_resonant)
        }
    
    def broadcast_resonance_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sincroniza estado entre todos os nós.
        """
        # Implementar broadcast
        return state

# Singleton global
_nccl_wrapper = NCCLResonanceWrapper()

def get_nccl_wrapper() -> NCCLResonanceWrapper:
    return _nccl_wrapper
