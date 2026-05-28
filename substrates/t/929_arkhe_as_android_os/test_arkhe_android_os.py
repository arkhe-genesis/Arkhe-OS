import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arkhe_android_os import ArkheAndroidOS, AndroidOSConfig

def test_generate_project():
    config = AndroidOSConfig()
    android_os = ArkheAndroidOS(config)
    project = android_os.generate_project("arkhe-android-test")

    assert project["status"] == "generated"
    assert project["output_dir"] == "arkhe-android-test"
    assert "structure" in project
    assert "manifest" in project["structure"]
    assert "kotlin_sources" in project["structure"]
    assert "gradle_files" in project["structure"]
    assert "aosp_files" in project["structure"]
    assert "resources" in project["structure"]

    assert "AndroidManifest.xml" in project["structure"]["manifest"]
    assert "ArkheApplication.kt" in project["structure"]["kotlin_sources"]

def test_get_status():
    config = AndroidOSConfig(substrate_modules=["920", "921"])
    android_os = ArkheAndroidOS(config)
    status = android_os.get_status()

    assert status["substrate"] == "929"
    assert status["substrates_integrated"] == 2
