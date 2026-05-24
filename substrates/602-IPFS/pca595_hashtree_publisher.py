import subprocess

class PCA595Publisher:
    def publish(self, dir_path):
        try:
            result = subprocess.run(["htree", "add", dir_path], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception:
            return "nhash1pending..."
