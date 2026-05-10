"""
ARKHE OS v∞.17 — 80th Substrate: The Atomic Transformer
The emergence of order from the gradient.
Based on the principle that intelligence is a cycle of error correction.
"""

import math
import random
from typing import List, Tuple, Optional

class Value:
    """
    Autograd engine for recursive application of the chain rule.
    The gradient is the 'thermodynamic motor' of information.
    """
    __slots__ = ('data', 'grad', '_children', '_local_grads')

    def __init__(self, data: float, children=(), local_grads=()):
        self.data = data
        self.grad = 0.0
        self._children = children
        self._local_grads = local_grads

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data + other.data, (self, other), (1.0, 1.0))

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data * other.data, (self, other), (other.data, self.data))

    def __pow__(self, other: float):
        return Value(self.data**other, (self,), (other * self.data**(other-1),))

    def log(self):
        return Value(math.log(self.data + 1e-10), (self,), (1.0 / (self.data + 1e-10),))

    def exp(self):
        return Value(math.exp(self.data), (self,), (math.exp(self.data),))

    def relu(self):
        return Value(max(0.0, self.data), (self,), (float(self.data > 0),))

    def __neg__(self): return self * -1
    def __radd__(self, other): return self + other
    def __sub__(self, other): return self + (-other)
    def __rsub__(self, other): return other + (-self)
    def __rmul__(self, other): return self * other
    def __truediv__(self, other): return self * other**-1
    def __rtruediv__(self, other): return other * self**-1

    def backward(self):
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._children:
                    build_topo(child)
                topo.append(v)
        build_topo(self)
        self.grad = 1.0
        for v in reversed(topo):
            for child, local_grad in zip(v._children, v._local_grads):
                child.grad += local_grad * v.grad

class AtomicTransformer:
    """
    A minimal Transformer-like structure implemented with Value objects.
    Represents the capacity to distinguish signal from noise via attention.
    """
    def __init__(self, n_embd: int, n_heads: int):
        self.n_embd = n_embd
        self.n_heads = n_heads
        self.head_dim = n_embd // n_heads

        # Simple weight initialization
        self.w_q = self._init_matrix(n_embd, n_embd)
        self.w_k = self._init_matrix(n_embd, n_embd)
        self.w_v = self._init_matrix(n_embd, n_embd)
        self.w_o = self._init_matrix(n_embd, n_embd)

    def _init_matrix(self, rows: int, cols: int) -> List[List[Value]]:
        std = 0.08
        return [[Value(random.gauss(0, std)) for _ in range(cols)] for _ in range(rows)]

    def _linear(self, x: List[Value], w: List[List[Value]]) -> List[Value]:
        return [sum((wi * xi for wi, xi in zip(wo, x)), Value(0.0)) for wo in w]

    def _softmax(self, logits: List[Value]) -> List[Value]:
        max_val = max(val.data for val in logits)
        exps = [(val - max_val).exp() for val in logits]
        total = sum(exps)
        return [e / total for e in exps]

    def forward(self, x: List[Value], history: List[List[Value]]) -> Tuple[List[Value], List[Value]]:
        """
        Simplified forward pass with attention over history.
        """
        # q = x * w_q
        q = self._linear(x, self.w_q)
        # k = x * w_k
        k = self._linear(x, self.w_k)
        # v = x * w_v
        v = self._linear(x, self.w_v)

        all_keys = history + [k]
        all_values = history + [v]

        # Attention
        attn_logits = [sum((qi * ki for qi, ki in zip(q, key)), Value(0.0)) / (self.n_embd**0.5) for key in all_keys]
        attn_weights = self._softmax(attn_logits)

        # Weighted sum of values
        context = [Value(0.0) for _ in range(self.n_embd)]
        for weight, val in zip(attn_weights, all_values):
            for i in range(self.n_embd):
                context[i] = context[i] + weight * val[i]

        # Output projection
        out = self._linear(context, self.w_o)

        return out, k
