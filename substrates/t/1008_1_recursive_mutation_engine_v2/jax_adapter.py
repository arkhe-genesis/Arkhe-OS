#!/usr/bin/env python3
"""Adaptador JAX/Flax — Substrato 1008.1"""
import jax
import jax.numpy as jnp
from flax import linen as nn
import numpy as np

class AdaptiveMutationEngineJAX(nn.Module):
    floor_etico: float = 0.005
    teto_theosis: float = 1.0

    def setup(self):
        self.generation = self.variable('state', 'gen', lambda: jnp.array(0, dtype=jnp.int32))
        self.singularity = self.variable('state', 'sing', lambda: jnp.array(0, dtype=jnp.int32))

    @staticmethod
    @jax.jit
    def step_fn(theosis_arr, stabilizer_arr, key, floor_etico, teto_theosis):
        avg_stab = jnp.mean(stabilizer_arr)
        keys = jax.random.split(key, len(stabilizer_arr))
        def update(i, arrs):
            t, s = arrs
            delta = jnp.where(s[i] > avg_stab, jax.random.uniform(keys[i], [], minval=0.03, maxval=0.06), jax.random.uniform(keys[i], [], minval=0.01, maxval=0.03))
            s = s.at[i].set(jnp.maximum(floor_etico, s[i] - delta))
            t = t.at[i].set(jnp.minimum(teto_theosis, t[i] + jax.random.uniform(keys[i], [], minval=0.01, maxval=0.05)))
            return (t, s)
        theosis_arr, stabilizer_arr = jax.lax.fori_loop(0, len(stabilizer_arr), lambda i, arrs: update(i, arrs), (theosis_arr, stabilizer_arr))
        return theosis_arr, stabilizer_arr

    def step(self, theosis_arr, stabilizer_arr):
        key = jax.random.PRNGKey(np.random.randint(0, 2**32))
        theosis_arr, stabilizer_arr = self.step_fn(theosis_arr, stabilizer_arr, key, self.floor_etico, self.teto_theosis)
        self.generation.value = self.generation.value + 1
        t = jnp.mean(theosis_arr)
        e = jnp.mean(stabilizer_arr)
        if t > 0.999 and e < 0.02: self.singularity.value = jnp.array(1, dtype=jnp.int32)
        return theosis_arr, stabilizer_arr

    def report(self, theosis_arr, stabilizer_arr):
        t = jnp.mean(theosis_arr)
        e = jnp.mean(stabilizer_arr)
        print(f"Gen {self.generation.value}: Theosis={t:.4f}, Entropia={e:.4f}", end="")
        if self.singularity.value == 1: print(f" ★ SINGULARIDADE AGI")
        else: print()
