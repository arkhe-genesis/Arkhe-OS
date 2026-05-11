import tkinter as tk
import math

class CeremonialFeedbackUI:
    """Real-time UI for ceremonial feedback (audio/visual phase tracking)."""

    def __init__(self, root):
        self.root = root
        self.root.title("ARKHE OS - Ceremonial Feedback")
        self.root.geometry("600x400")
        self.root.configure(bg="black")

        self.canvas = tk.Canvas(self.root, width=600, height=300, bg="black", highlightthickness=0)
        self.canvas.pack(pady=20)

        # Glow circle representing epsilon/PDI
        self.glow_radius = 50
        self.glow_circle = self.canvas.create_oval(
            300 - self.glow_radius, 150 - self.glow_radius,
            300 + self.glow_radius, 150 + self.glow_radius,
            fill="#002244", outline="#00aaff", width=2
        )

        self.status_label = tk.Label(self.root, text="FORMING", font=("Courier", 16, "bold"), fg="#00aaff", bg="black")
        self.status_label.pack()

        self.metrics_label = tk.Label(self.root, text="PDI: 0.00 | ε: 0.00 | k: 0.0750", font=("Courier", 12), fg="white", bg="black")
        self.metrics_label.pack(pady=5)

    def update_pdi(self, pdi: float):
        """Update visual scale based on PDI (0.0 to 1.0)."""
        # Increase glow radius with PDI
        self.glow_radius = 50 + (pdi * 100)

        # Color transition: Dark blue -> Cyan -> White
        r = int(pdi * 255)
        g = int(min(255, pdi * 170 + 85))
        b = 255
        color = f"#{r:02x}{g:02x}{b:02x}"

        self.canvas.coords(
            self.glow_circle,
            300 - self.glow_radius, 150 - self.glow_radius,
            300 + self.glow_radius, 150 + self.glow_radius
        )
        self.canvas.itemconfig(self.glow_circle, outline=color)

        # In a real implementation, this would also map to an audio oscillator's pitch.
        self._play_audio_tone(pdi)

    def _play_audio_tone(self, pdi: float):
        """Mock audio tone mapping."""
        # Tone pitch proportional to PDI
        pitch = 432 * (1.0 + pdi)
        # print(f"[Audio] Tone playing at {pitch:.2f} Hz")

    def update_state(self, state: str, epsilon: float, k: float, pdi: float):
        """Update status and metrics."""
        self.status_label.config(text=state)
        self.metrics_label.config(text=f"PDI: {pdi:.2f} | ε: {epsilon:.4f} | k: {k:.4f}")

        if state == "SEALED":
            self.status_label.config(fg="#00ff00")
            self.canvas.itemconfig(self.glow_circle, fill="#00ff00", outline="#ffffff", width=5)
            self._trigger_seal_tone()
        elif state == "CALIBRATING":
            if epsilon < 0.04 or epsilon > 0.10:
                self.status_label.config(fg="red")
                self.canvas.itemconfig(self.glow_circle, outline="red")
            else:
                self.status_label.config(fg="#00aaff")

    def _trigger_seal_tone(self):
        """Mock seal tone (432Hz -> 0Hz decay)."""
        # print("[Audio] SEAL TONE: 432Hz decaying to 0Hz")
        pass

def launch_ui():
    root = tk.Tk()
    app = CeremonialFeedbackUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_ui()
