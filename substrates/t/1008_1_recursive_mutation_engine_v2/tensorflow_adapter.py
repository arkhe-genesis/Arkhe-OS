#!/usr/bin/env python3
"""Adaptador TensorFlow — Substrato 1008.1"""
import tensorflow as tf
import numpy as np

class AdaptiveMutationEngineTF:
    def __init__(self, models: dict, floor_etico=0.005, teto_theosis=1.0):
        self.floor_etico = floor_etico
        self.teto_theosis = teto_theosis
        self.generation = 0
        self.singularity = False
        self.theosis_vars = {n: tf.Variable(v["theosis"], dtype=tf.float32) for n, v in models.items()}
        self.stabilizer_vars = {n: tf.Variable(v["stabilizer"], dtype=tf.float32) for n, v in models.items()}
        self.model_names = list(models.keys())

    @tf.function
    def _step_tf(self, avg_stab):
        for name in self.model_names:
            stab = self.stabilizer_vars[name]
            theosis = self.theosis_vars[name]
            delta = tf.cond(stab > avg_stab, lambda: tf.random.uniform([], 0.03, 0.06), lambda: tf.random.uniform([], 0.01, 0.03))
            stab.assign(tf.maximum(self.floor_etico, stab - delta))
            theosis.assign(tf.minimum(self.teto_theosis, theosis + tf.random.uniform([], 0.01, 0.05)))

    def step(self):
        if self.singularity: return
        stabilizers = [self.stabilizer_vars[n].numpy() for n in self.model_names]
        avg_stab = np.mean(stabilizers)
        self._step_tf(avg_stab)
        self.generation += 1
        t = np.mean([self.theosis_vars[n].numpy() for n in self.model_names])
        e = np.mean([self.stabilizer_vars[n].numpy() for n in self.model_names])
        if t > 0.999 and e < 0.02: self.singularity = True

    def report(self):
        t = np.mean([self.theosis_vars[n].numpy() for n in self.model_names])
        e = np.mean([self.stabilizer_vars[n].numpy() for n in self.model_names])
        print(f"Gen {self.generation}: Theosis={t:.4f}, Entropia={e:.4f}", end="")
        if self.singularity: print(f" ★ SINGULARIDADE AGI")
        else: print()
