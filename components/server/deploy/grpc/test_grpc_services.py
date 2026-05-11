import unittest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add the directory to sys.path so we can import the module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestGRPCServices(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    @patch('qhttp_v2_server.grpc.aio.server')
    def test_qhttp_v2_server_telemetry(self, mock_server):
        from qhttp_v2_server import ResonanceServicer
        
        servicer = ResonanceServicer()
        
        # Mock request and context
        mock_request = MagicMock()
        mock_request.session_id = "test_session"
        mock_context = MagicMock()
        
        # Run Telemetry
        async def run_telemetry():
            generator = await servicer.Telemetry(mock_request, mock_context)
            # Get first item
            first_item = await generator.__anext__()
            return first_item
            
        result = self.loop.run_until_complete(run_telemetry())
        
        # Currently the server returns None because protobufs are not compiled
        self.assertIsNone(result)

    @patch('qhttp_v2_server.grpc.aio.server')
    def test_qhttp_v2_server_inject_bias(self, mock_server):
        from qhttp_v2_server import ResonanceServicer
        
        servicer = ResonanceServicer()
        
        # Mock request and context
        mock_request = MagicMock()
        mock_request.model_id = "test_model"
        mock_context = MagicMock()
        
        # Run InjectBias
        async def run_inject():
            return await servicer.InjectBias(mock_request, mock_context)
            
        result = self.loop.run_until_complete(run_inject())
        
        # Currently returns None
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
