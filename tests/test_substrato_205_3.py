import pytest
import subprocess
import os

def test_substrato_205_3_toom():
    # Build out-of-source
    os.makedirs("arkhe-cpp/build", exist_ok=True)
    build_cmd = ["cmake", ".."]
    subprocess.run(build_cmd, cwd="arkhe-cpp/build", check=True)
    make_cmd = ["make"]
    subprocess.run(make_cmd, cwd="arkhe-cpp/build", check=True)

    # Run
    run_cmd = ["./test_toom"]
    result = subprocess.run(run_cmd, cwd="arkhe-cpp/build", capture_output=True, text=True, check=True)

    output = result.stdout
    assert "TOOM-6.5 (12 pontos" in output
    assert "TOOM-8.5 (16 pontos" in output
    assert "Avalia\u00e7\u00e3o e multiplica\u00e7\u00f5es pontuais conclu\u00eddas." in output
    assert "Substrato 205.3" in output
    assert "Operacional" in output
