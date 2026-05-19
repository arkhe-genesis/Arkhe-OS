from pathlib import Path

def test_arkhe_analytics():
    assert Path("arkhe-analytics/PhiCAnalyticsCollector.kt").exists()

def test_arkhe_fips():
    assert Path("arkhe-fips/FIPSLabCertificationManager.kt").exists()

def test_arkhe_core_shared():
    assert Path("arkhe-core-shared/src/lib.rs").exists()

def test_arkhe_ios():
    assert Path("arkhe-ios/Sources/ArkheCore/ArkheCore.swift").exists()
