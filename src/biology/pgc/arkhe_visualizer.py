import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

class ArkheVisualizer:
    def __init__(self, style='dark'):
        if style == 'dark':
            plt.style.use('dark_background')
        self.colors = {'class_b': '#4ECDC4', 'class_a': '#FF6B6B'}

    def plot_kuramoto_compass(self, phase_data, pathway_name="Genome Wide", output_file='kuramoto_compass.png'):
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='polar')

        phases = phase_data['theta'].values
        weights = phase_data['weight'].values

        if len(phases) > 2000:
            idx = np.random.choice(len(phases), 2000, replace=False)
            phases = phases[idx]
            weights = weights[idx]

        ax.scatter(phases, weights, alpha=0.5, s=10, c=phases, cmap='hsv')

        complex_sum = np.sum(weights * np.exp(1j * phases))
        z = complex_sum / np.sum(weights)
        lambda_2 = np.abs(z)
        angle = np.angle(z)

        ax.annotate('', xy=(angle, lambda_2 * np.max(weights)), xytext=(0, 0),
                    arrowprops=dict(facecolor='white', edgecolor='gold', width=3))

        ax.set_title(f"Kuramoto Compass: {pathway_name}\nλ₂ = {lambda_2:.4f}", fontsize=14)
        plt.savefig(output_file)
        plt.close()

    def plot_null_test(self, test_results, output_file='null_test.png'):
        plt.figure(figsize=(10, 6))
        sns.histplot(np.random.normal(test_results['null_mean'], test_results['null_std'], 1000),
                     kde=True, label='Null Distribution')
        plt.axvline(test_results['real_lambda'], color='red', linestyle='--',
                    label=f'Observed λ₂ ({test_results["real_lambda"]:.4f})')
        plt.title("Null Coherence Test")
        plt.legend()
        plt.savefig(output_file)
        plt.close()

    def plot_phase_difference_radar(self, common_df, disorder_a="SCZ", disorder_b="BIP", output_file='phase_radar.png'):
        diffs = common_df['theta_A'] - common_df['theta_B']
        diffs = (diffs + np.pi) % (2 * np.pi) - np.pi

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='polar')

        n_bins = 36
        counts, bins = np.histogram(diffs, bins=n_bins, range=(-np.pi, np.pi))
        ax.bar(bins[:-1], counts, width=2*np.pi/n_bins, color='#4ECDC4', alpha=0.7)

        ax.set_title(f"Phase Difference: {disorder_a} vs {disorder_b}", fontsize=14)
        plt.savefig(output_file)
        plt.close()

    def plot_gene_overlap_venn(self, set_a, set_b, labels=("SCZ", "BIP"), output_file='venn_overlap.png'):
        try:
            from matplotlib_venn import venn2
            plt.figure(figsize=(8, 8))
            venn2([set_a, set_b], set_labels=labels)
            plt.title("Mapped Gene Overlap")
            plt.savefig(output_file)
            plt.close()
        except ImportError:
            print("matplotlib-venn not installed. Skipping Venn plot.")
