import pytest
import subprocess
import time
import urllib.request
import json

def test_qbus_transmission():
    # Start the sidecar in background
    sidecar = subprocess.Popen(["python3", "-m", "uvicorn", "sidecars.qbus.qbus_sidecar:app", "--port", "8081"])
    time.sleep(2)

    try:
        req = urllib.request.Request("http://localhost:8081/transmit", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"message": "Test Message"}).encode('utf-8')

        with urllib.request.urlopen(req, data=data) as response:
            assert response.status == 200
            response_data = json.loads(response.read().decode('utf-8'))
            assert "photon_state" in response_data
            assert response_data["status"] in ["transmitted", "transmitted_mock"]
    finally:
        sidecar.terminate()
        sidecar.wait()
