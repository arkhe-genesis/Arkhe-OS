import os
import subprocess
import sys
import time

def main():
    print("🜏 Initializing Arkhe ACE-Step UI Bridge...", file=sys.stderr)

    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arkhe-ace-step-ui")

    if not os.path.exists(ui_path):
        print(f"Error: Directory {ui_path} not found.", file=sys.stderr)
        sys.exit(1)

    print("🜏 Installing frontend dependencies...", file=sys.stderr)
    subprocess.run(["npm", "install"], cwd=ui_path, check=True)

    server_path = os.path.join(ui_path, "server")
    if os.path.exists(server_path):
        print("🜏 Installing server dependencies...", file=sys.stderr)
        subprocess.run(["npm", "install"], cwd=server_path, check=True)

        env_example = os.path.join(server_path, ".env.example")
        env_file = os.path.join(server_path, ".env")
        if os.path.exists(env_example) and not os.path.exists(env_file):
            print("🜏 Copying .env.example to .env...", file=sys.stderr)
            import shutil
            shutil.copy2(env_example, env_file)

    print("🜏 Starting Arkhe ACE-Step UI...", file=sys.stderr)
    try:
        # Instead of waiting, we run the start process
        process = subprocess.Popen(
            ["npm", "start"],
            cwd=ui_path,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        print(f"🜏 Arkhe ACE-Step UI started with PID: {process.pid}", file=sys.stderr)
        process.wait()
    except KeyboardInterrupt:
        print("🜏 Shutting down Arkhe ACE-Step UI...", file=sys.stderr)
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
