import random, time, math

def fpga_read_event(args: dict) -> dict:
    """Le o proximo evento da FIFO da FPGA."""
    amplitude = random.gauss(500, 150)
    integral = random.gauss(2000, 500)
    return {
        "timestamp_ns": int(time.time_ns()),
        "amplitude_mV": max(0, int(amplitude)),
        "integral_nVs": max(0, int(integral)),
        "channel": args.get("channel", 0),
        "fpga_status": "OK",
        "fifo_fill_pct": random.uniform(10, 60)
    }

def fpga_get_status(args: dict) -> dict:
    """Retorna o status do sistema FPGA."""
    return {
        "fpga_model": "Xilinx Artix-7",
        "pcie_link": "Gen2 x4 OK",
        "adc_locked": True,
        "temperature_c": random.uniform(35, 55),
        "events_total": random.randint(100000, 999999),
        "uptime_hours": random.uniform(24, 720),
        "cryo_status": "20.0K nominal"
    }

def fpga_set_threshold(args: dict) -> dict:
    """Define o limiar de deteccao do ADC."""
    new_threshold = args.get("value", 200)
    return {
        "previous_threshold": 200,
        "new_threshold": new_threshold,
        "status": "updated"
    }

def fpga_correlate_events(args: dict) -> dict:
    """Correlaciona eventos entre multiplos canais."""
    node_id = args.get("node_id", 0)
    return {
        "correlated": random.random() > 0.3,
        "node_id": node_id,
        "coincidence_window_ns": 100,
        "events_in_window": random.randint(0, 5),
        "estimated_direction": {
            "theta_deg": random.uniform(0, 180),
            "phi_deg": random.uniform(0, 360)
        }
    }

# Registro das ferramentas
FPGA_TOOLS = {
    "fpga_read_event": {
        "function": fpga_read_event,
        "description": "Le o proximo evento de particula da FIFO da FPGA"
    },
    "fpga_get_status": {
        "function": fpga_get_status,
        "description": "Retorna o status do sistema FPGA/DAQ"
    },
    "fpga_set_threshold": {
        "function": fpga_set_threshold,
        "description": "Define o limiar de deteccao do ADC em counts"
    },
    "fpga_correlate_events": {
        "function": fpga_correlate_events,
        "description": "Correlaciona eventos entre canais para triangulacao"
    }
}