from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict
import io
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

# Set headless backend for Matplotlib
matplotlib.use('Agg')

from arkhe_os.simulations.baroclinic_vorticity_cire import BaroclinicCIRESimulator

router = APIRouter(prefix="/v1/simulations", tags=["Simulations"])

class SimMetrics(BaseModel):
    time: List[float]
    omega_max: List[float]
    omega_mean: List[float]

class SimResult(BaseModel):
    metrics: SimMetrics
    status: str

@router.post("/baroclinic/run", response_model=SimResult)
async def run_baroclinic_sim(steps: int = 500, gig_pulse_at: int = 50):
    """
    Executa a simulação baroclínica e retorna métricas.
    """
    try:
        sim = BaroclinicCIRESimulator(grid_size=128)
        history, omega, vx, vy = sim.run_simulation(steps=steps, gig_pulse_at=gig_pulse_at)

        return SimResult(
            metrics=SimMetrics(
                time=history["time"],
                omega_max=history["omega_max"],
                omega_mean=history["omega_mean"]
            ),
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/baroclinic/plot")
async def get_baroclinic_plot(steps: int = 500, gig_pulse_at: int = 50):
    """
    Executa a simulação e retorna o gráfico como uma imagem PNG (thread-safe).
    """
    try:
        sim = BaroclinicCIRESimulator(grid_size=128)
        history, omega, vx, vy = sim.run_simulation(steps=steps, gig_pulse_at=gig_pulse_at)

        # Use object-oriented API for thread safety
        fig = Figure(figsize=(12, 5))
        canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)

        ax1 = fig.add_subplot(1, 2, 1)
        im = ax1.imshow(omega.T, extent=[-100, 100, -100, 100], cmap='RdBu_r', origin='lower')
        fig.colorbar(im, ax=ax1, label='Vorticidade ω_z [s⁻¹]')
        ax1.set_title('Vorticidade após Pulso GIG')
        ax1.set_xlabel('x [µm]')
        ax1.set_ylabel('y [µm]')

        ax2 = fig.add_subplot(1, 2, 2)
        ax2.plot(np.array(history["time"])*1e9, history["omega_max"], label='Max |ω|')
        ax2.plot(np.array(history["time"])*1e9, history["omega_mean"], label='Mean |ω|')
        ax2.set_xlabel('Tempo [ns]')
        ax2.set_ylabel('Vorticidade [s⁻¹]')
        ax2.legend()
        ax2.grid(True)
        ax2.set_title('Evolução Temporal da Vorticidade')

        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)

        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
