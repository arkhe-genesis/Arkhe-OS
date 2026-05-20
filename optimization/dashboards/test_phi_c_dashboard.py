import unittest
from phi_c_dashboard import fetch_status
from unittest.mock import patch

class TestDashboard(unittest.TestCase):
    @patch('phi_c_dashboard.requests.get')
    def test_fetch_status(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"avg_phi_c": 0.95}

        status = fetch_status()
        self.assertEqual(status["avg_phi_c"], 0.95)

if __name__ == "__main__":
    unittest.main()
