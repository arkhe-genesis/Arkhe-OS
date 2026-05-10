# visualization.py
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

def plot_results(times, phases_open, phases_closed, controls=None, save_path=None):
    plt.figure(figsize=(10, 6))
    plt.plot(times, phases_open, label='Open Loop')
    plt.plot(times, phases_closed, label='Closed Loop (Damper)')
    plt.xlabel('Time (s)')
    plt.ylabel('Fisher Phase (rad)')
    plt.legend()
    if save_path: plt.savefig(save_path)
    # plt.show()

def plot_spectrum(phases, dt, label='', ax=None, color='b'):
    if ax is None: fig, ax = plt.subplots()
    f, Pxx = signal.periodogram(np.array(phases) - np.mean(phases), fs=1/dt)
    ax.semilogy(f, Pxx, color=color, label=label)
    ax.legend()
