# compare_pid_lqr.py
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../python'))
from fisher_sim.simulation import CathedralSimulation
from fisher_sim.visualization import plot_results

def main():
    print("Comparing PID vs LQR Damping...")
    sim_pid = CathedralSimulation(duration=50.0, dt=0.1, controller_type='pid')
    _, _, ph_pid, _ = sim_pid.run()

    sim_lqr = CathedralSimulation(duration=50.0, dt=0.1, controller_type='lqr')
    times, ph_open, ph_lqr, _ = sim_lqr.run()

    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    plt.plot(times, ph_open, label='No Control', color='gray', alpha=0.5)
    plt.plot(times, ph_pid, label='PID Control')
    plt.plot(times, ph_lqr, label='LQR Control')
    plt.legend()
    plt.savefig('pid_vs_lqr.png')
    print("Comparison complete. Results saved to pid_vs_lqr.png")

if __name__ == "__main__":
    main()
