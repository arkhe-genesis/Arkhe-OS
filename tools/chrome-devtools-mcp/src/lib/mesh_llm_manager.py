import base64
import json
import subprocess
import sys
import os
import shutil
import threading

# Default to searching for it in the path
MESH_LLM_BIN = os.getenv("MESH_LLM_BIN", "mesh-llm")
# The join token should be provided as an environment variable
MESH_LLM_JOIN_TOKEN = os.getenv("MESH_LLM_JOIN_TOKEN")
MESH_LLM_MODEL = os.getenv("MESH_LLM_MODEL")

class MeshLLMManager:
    def __init__(self, token=None, model=None):
        self.token = token or MESH_LLM_JOIN_TOKEN
        self.model = model or MESH_LLM_MODEL
        self.decoded_token = self._decode_token(self.token) if self.token else None

    def _decode_token(self, token):
        try:
            # Handle potential padding issues
            missing_padding = len(token) % 4
            if missing_padding:
                token += '=' * (4 - missing_padding)
            decoded = base64.b64decode(token).decode('utf-8')
            return json.loads(decoded)
        except Exception as e:
            print(f"Error decoding token: {e}")
            return None

    def _stream_output(self, pipe, prefix):
        for line in iter(pipe.readline, ''):
            if line:
                print(f"[{prefix}] {line.strip()}", flush=True)

    def join_mesh(self, client=True, model=None):
        bin_path = shutil.which(MESH_LLM_BIN)
        if not bin_path:
            print(f"Error: {MESH_LLM_BIN} not found in PATH")
            return False

        if not self.token:
            print("Error: No join token provided")
            return False

        cmd = [bin_path]

        # Use provided model or instance default
        active_model = model or self.model

        if active_model:
            cmd.extend(["--model", active_model])
        elif client:
            cmd.append("--client")

        cmd.extend(["--join", self.token])

        print(f"Joining mesh with command: {' '.join(cmd)}", flush=True)
        try:
            # We run it and wait for it to finish, streaming logs
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            stdout_thread = threading.Thread(target=self._stream_output, args=(process.stdout, "STDOUT"))
            stderr_thread = threading.Thread(target=self._stream_output, args=(process.stderr, "STDERR"))

            stdout_thread.start()
            stderr_thread.start()

            print(f"Started mesh-llm process with PID: {process.pid}. Waiting for exit...", flush=True)
            exit_code = process.wait()

            stdout_thread.join()
            stderr_thread.join()

            print(f"mesh-llm process exited with code: {exit_code}", flush=True)
            return exit_code == 0
        except Exception as e:
            print(f"Error starting mesh-llm: {e}", flush=True)
            return False

    def get_status(self):
        bin_path = shutil.which(MESH_LLM_BIN)
        if not bin_path:
            return f"Error: {MESH_LLM_BIN} not found in PATH"

        try:
            result = subprocess.run([bin_path, "status"], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Error getting status: {e}"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Arkhe(n) Mesh-LLM Manager")
    parser.add_argument("--join", type=str, help="Token to join the mesh (overrides MESH_LLM_JOIN_TOKEN)")
    parser.add_argument("--model", type=str, help="Model to serve (overrides MESH_LLM_MODEL)")
    parser.add_argument("--status", action="store_true", help="Get mesh status")

    args = parser.parse_args()

    manager = MeshLLMManager(args.join, args.model)

    if args.status:
        print(manager.get_status())
    else:
        success = manager.join_mesh(model=args.model)
        if not success:
            sys.exit(1)
