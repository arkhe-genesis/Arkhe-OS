import asyncio
import unittest
from unittest.mock import MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bridge')))

from arkhe_ethereum_bridge import ArkheEthereumBridge

class TestBridgeLoop(unittest.IsolatedAsyncioTestCase):
    @patch('arkhe_ethereum_bridge.Web3')
    async def test_oracle_loop(self, MockWeb3):
        bridge = ArkheEthereumBridge("http://localhost:8545", "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")

        # Mock the bridge contract
        mock_contract = MagicMock()
        mock_functions = MagicMock()
        mock_tx_build = MagicMock()
        mock_tx_build.build_transaction.return_value = {'to': '0x123', 'data': '0x'}
        mock_functions.anchorSeal.return_value = mock_tx_build
        mock_contract.functions = mock_functions

        bridge.bridge_contract = mock_contract

        # Mock the transaction sending
        mock_receipt = MagicMock()
        mock_receipt.transactionHash = b'tx_hash_123'
        bridge._send_transaction = MagicMock(return_value=mock_receipt)

        # Create an event queue and put a test event
        queue = asyncio.Queue()
        test_event = {
            'seal_hash': b'0' * 32,
            'phi_c_score': 100,
            'metadata_uri': 'ipfs://test_metadata'
        }
        await queue.put(test_event)

        # Run the loop as a task
        task = asyncio.create_task(bridge.oracle_loop(queue))

        # Wait for queue to be processed
        await queue.join()

        # Cancel the infinite loop
        task.cancel()

        # Assertions
        mock_functions.anchorSeal.assert_called_once_with(b'0' * 32, 100, 'ipfs://test_metadata')
        bridge._send_transaction.assert_called_once()
        print("Oracle loop test passed: Event anchored successfully.")

if __name__ == '__main__':
    unittest.main()
