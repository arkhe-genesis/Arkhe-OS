# run_basic_sim.py
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../python'))
from fisher_sim.simulation import CathedralSimulation
from fisher_sim.visualization import plot_results

def main():
    print("Running Basic Fisher Interferometer Simulation...")
    sim = CathedralSimulation(duration=50.0, dt=0.1, controller_type='lqr')
    times, ph_open, ph_closed, controls = sim.run()
    plot_results(times, ph_open, ph_closed, save_path='fisher_sim_results.png')
    print("Simulation complete. Results saved to fisher_sim_results.png")

if __name__ == "__main__":
    main()
