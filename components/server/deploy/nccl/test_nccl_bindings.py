import unittest
from unittest.mock import patch, MagicMock
import torch
import sys
import os

# Add the directory to sys.path so we can import the module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestNCCLBindings(unittest.TestCase):
    @patch('torch.distributed.is_initialized', return_value=True)
    @patch('torch.distributed.broadcast')
    @patch('ctypes.CDLL')
    def test_initialization(self, mock_cdll, mock_broadcast, mock_is_initialized):
        # Mock the C library
        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib
        
        # Mock the C functions
        mock_lib.get_nccl_unique_id = MagicMock()
        mock_lib.init_nccl_comm = MagicMock(return_value=12345)
        mock_lib.create_nccl_calculator = MagicMock(return_value=67890)
        
        from nccl_bindings import NCCLResonanceWrapper
        
        wrapper = NCCLResonanceWrapper()
        wrapper.initialize(rank=0, world_size=4, device=0)
        
        self.assertTrue(wrapper._initialized)
        self.assertEqual(wrapper._calculator, 67890)
        
        # Verify C functions were called
        mock_lib.get_nccl_unique_id.assert_called_once()
        mock_lib.init_nccl_comm.assert_called_once()
        mock_lib.create_nccl_calculator.assert_called_once_with(12345, 0, 4, 0)
        mock_broadcast.assert_called_once()

    @patch('torch.distributed.is_initialized', return_value=True)
    @patch('torch.distributed.broadcast')
    @patch('ctypes.CDLL')
    def test_compute_global_resonance(self, mock_cdll, mock_broadcast, mock_is_initialized):
        # Mock the C library
        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib
        
        # Mock the result structure
        class MockResult:
            phase = 1.57
            omega_prime = 0.95
            sigma = 0.1
            damping = 0.9
            rho_1_global = 0.5
            rho_2_global = 0.8
            is_resonant = True
            
        mock_lib.compute_global_resonance = MagicMock(return_value=MockResult())
        
        from nccl_bindings import NCCLResonanceWrapper
        
        wrapper = NCCLResonanceWrapper()
        wrapper.initialize(rank=0, world_size=4, device=0)
        
        # Create dummy tensor
        local_params = torch.randn(100)
        
        result = wrapper.compute_global_resonance(
            local_params=local_params,
            global_tokens=1000000,
            local_loss=2.5
        )
        
        self.assertEqual(result["phase"], 1.57)
        self.assertEqual(result["is_resonant"], True)
        self.assertEqual(result["omega_prime"], 0.95)
        
        mock_lib.compute_global_resonance.assert_called_once()

if __name__ == '__main__':
    unittest.main()
