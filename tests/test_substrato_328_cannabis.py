import sys
import os
import pytest
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

cannabis_triad = importlib.import_module("src.32_luciferase.328_biofotonica_ontologica.cannabis_triad")
CannabisBiophotonReporter = cannabis_triad.CannabisBiophotonReporter
CannabinoidBiosensorKM206 = cannabis_triad.CannabinoidBiosensorKM206
PhotodynamicCannabinoidTherapy = cannabis_triad.PhotodynamicCannabinoidTherapy

def test_cannabis_biophoton_reporter():
    reporter = CannabisBiophotonReporter()
    assert abs(reporter.phic - 0.500294) < 1e-6

    reporter.report_expression("THC_synthase_promoter", 0.7480, 528)
    reporter.report_expression("CBD_synthase_promoter", 0.8096, 528)
    reporter.report_expression("CBG_synthase_promoter", 0.3960, 528)

    assert reporter.thc_level > 0.007
    assert reporter.cbd_level > 0.008
    assert reporter.cbg_level > 0.003
    assert not reporter.is_ghost_preserved()

def test_cannabinoid_biosensor():
    sensor = CannabinoidBiosensorKM206()

    res1 = sensor.detect_sample("SAMPLE-001", 150.0)
    assert res1["detected"] is True
    assert res1["risk"] == "POSITIVE"

    res2 = sensor.detect_sample("SAMPLE-002", 45.0)
    assert res2["detected"] is False
    assert res2["risk"] == "NEGATIVE"

    res3 = sensor.detect_sample("SAMPLE-003", 500.0, ["JWH-018", "AM-2201"])
    assert res3["detected"] is True
    assert res3["risk"] == "CRITICAL"
    assert "JWH-018" in res3["scras"]

    res5 = sensor.detect_sample("SAMPLE-005", 80.0, ["5F-ADB"])
    assert res5["detected"] is False
    assert res5["risk"] == "CRITICAL"
    assert "5F-ADB" in res5["scras"]

def test_pdt_c_oncology():
    pdtc = PhotodynamicCannabinoidTherapy()

    res1 = pdtc.apply_session("TUMOR-A-001", 50, 10.0, 250)
    # expected efficacy roughly: (10 * 50) / (250 * 10) = 500 / 2500 = 0.2 -> 20%
    assert abs(res1["efficacy_pct"] - 20.0) < 1e-1
    assert res1["total_damage"] == 2.5

    res2 = pdtc.apply_session("TUMOR-C-003", 30, 8.0, 150)
    # expected efficacy roughly: (8 * 30) / (150 * 10) = 240 / 1500 = 0.16 -> 16%
    assert abs(res2["efficacy_pct"] - 16.0) < 1e-1
