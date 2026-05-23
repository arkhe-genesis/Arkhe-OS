import subprocess
import os

def test_unified_container():
    result = subprocess.run(["python3", "substrates/500-599_advanced/substrato_unified_container/substrato_unified_container.py"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Canonized output saved to" in result.stdout
    assert "UNIFIED-CONTAINER" in result.stdout
    assert "v∞.Ω.∇+++" in result.stdout

if __name__ == '__main__':
    test_unified_container()
    print("Tests passed!")
