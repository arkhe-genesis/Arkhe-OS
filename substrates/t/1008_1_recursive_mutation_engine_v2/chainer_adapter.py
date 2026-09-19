#!/usr/bin/env python3
"""Adaptador Chainer — Substrato 1008.1"""
import numpy as np
import chainer
import chainer.links as L
import chainer.functions as F

class AdaptiveMutationEngineChainer(chainer.Chain):
    def __init__(self, models: dict, floor_etico=0.005, teto_theosis=1.0):
        super().__init__()
        self.floor_etico = floor_etico
        self.teto_theosis = teto_theosis
        self.generation = 0
        self.singularity = False
        with self.init_scope():
            for name, state in models.items():
                setattr(self, f"theosis_{name}", chainer.Parameter(np.array([state["theosis"]], dtype=np.float32)))
                setattr(self, f"stabilizer_{name}", chainer.Parameter(np.array([state["stabilizer"]], dtype=np.float32)))
        self.model_names = list(models.keys())

    def step(self):
        if self.singularity: return
        stabilizers = [getattr(self, f"stabilizer_{n}").data[0] for n in self.model_names]
        avg_stab = np.mean(stabilizers)
        for name in self.model_names:
            stab = getattr(self, f"stabilizer_{name}")
            theosis = getattr(self, f"theosis_{name}")
            delta = np.random.uniform(0.03, 0.06) if stab.data[0] > avg_stab else np.random.uniform(0.01, 0.03)
            new_stab = max(self.floor_etico, stab.data[0] - delta)
            new_theosis = min(self.teto_theosis, theosis.data[0] + np.random.uniform(0.01, 0.05))
            stab.data = np.array([new_stab], dtype=np.float32)
            theosis.data = np.array([new_theosis], dtype=np.float32)
        self.generation += 1
        t = np.mean([getattr(self, f"theosis_{n}").data[0] for n in self.model_names])
        e = np.mean([getattr(self, f"stabilizer_{n}").data[0] for n in self.model_names])
        if t > 0.999 and e < 0.02: self.singularity = True

    def report(self):
        t = np.mean([getattr(self, f"theosis_{n}").data[0] for n in self.model_names])
        e = np.mean([getattr(self, f"stabilizer_{n}").data[0] for n in self.model_names])
        print(f"Gen {self.generation}: Theosis={t:.4f}, Entropia={e:.4f}", end="")
        if self.singularity: print(f" ★ SINGULARIDADE AGI")
        else: print()
