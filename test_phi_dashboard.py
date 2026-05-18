import pytest
import numpy as np
from substrate_202.dashboards.phi_composite_dashboard import (
    LayerType, LayerPhiCMonitor, CompositePhiCCalculator, PhiCCompositeDashboard
)

def test_layer_monitor():
    monitor = LayerPhiCMonitor(LayerType.MAINFRAME_ACID)
    metric = monitor.update_metric(0.9995, 0.999, 10.0, 0.0005)

    assert metric.phi_c_value == 0.9995
    assert metric.latency_ms == 10.0

    alert, reason = monitor.check_alert_thresholds(metric)
    assert not alert

    bad_metric = monitor.update_metric(0.90, 0.90, 100.0, 0.05)
    alert, reason = monitor.check_alert_thresholds(bad_metric)
    assert alert

def test_composite_calculator():
    calc = CompositePhiCCalculator()
    metrics = {
        LayerType.MAINFRAME_ACID: LayerPhiCMonitor(LayerType.MAINFRAME_ACID).get_current_metric(),
        LayerType.BEAVER_LOGIC: LayerPhiCMonitor(LayerType.BEAVER_LOGIC).get_current_metric(),
        LayerType.TOKEN_ARKHE_INTENTION: LayerPhiCMonitor(LayerType.TOKEN_ARKHE_INTENTION).get_current_metric(),
        LayerType.TEMPORALCHAIN_META: LayerPhiCMonitor(LayerType.TEMPORALCHAIN_META).get_current_metric(),
    }

    composite = calc.calculate_composite_phi_c(metrics)
    assert 0.0 <= composite <= 1.0

@pytest.mark.asyncio
async def test_dashboard():
    dashboard = PhiCCompositeDashboard()

    dashboard.simulate_layer_update(LayerType.MAINFRAME_ACID, 0.9995, 0.999, 12.5, 0.0005)
    dashboard.simulate_layer_update(LayerType.BEAVER_LOGIC, 0.997, 0.995, 85.2, 0.008)
    dashboard.simulate_layer_update(LayerType.TOKEN_ARKHE_INTENTION, 0.96, 0.94, 450.0, 0.03)
    dashboard.simulate_layer_update(LayerType.TEMPORALCHAIN_META, 0.9999, 0.9999, 2100.0, 0.0002)

    report = await dashboard._generate_and_publish_report()

    assert report.composite_phi_c > 0.95
    assert report.alert_level in ["normal", "warning"]
