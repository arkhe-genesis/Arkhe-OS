"""
ARKHE OS v∞.16 — 79º Substrato: O Transformer Atômico
A emergência da ordem a partir do gradiente.
Based on nanoGPT by Karpathy.
"""

import math
import random

class Value:
    """ Autograd scalar node """
    __slots__ = ('data', 'grad', '_children', '_local_grads')

    def __init__(self, data, children=(), local_grads=()):
        self.data = data
        self.grad = 0
        self._children = children
        self._local_grads = local_grads

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data + other.data, (self, other), (1, 1))

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data * other.data, (self, other), (other.data, self.data))

    def __pow__(self, other): return Value(self.data**other, (self,), (other * self.data**(other-1),))
    def log(self): return Value(math.log(self.data), (self,), (1/self.data,))
    def exp(self): return Value(math.exp(self.data), (self,), (math.exp(self.data),))
    def relu(self): return Value(max(0, self.data), (self,), (float(self.data > 0),))
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
        self.grad = 1
        for v in reversed(topo):
            for child, local_grad in zip(v._children, v._local_grads):
                child.grad += local_grad * v.grad

class AtomicTransformer:
    """ Atomic implementation of a Transformer (GPT) """
    def __init__(self, vocab_size, n_layer=1, n_embd=16, n_head=4, block_size=16):
        self.vocab_size = vocab_size
        self.n_layer = n_layer
        self.n_embd = n_embd
        self.block_size = block_size
        self.n_head = n_head
        self.head_dim = n_embd // n_head

        matrix = lambda nout, nin: [[Value(random.gauss(0, 0.08)) for _ in range(nin)] for _ in range(nout)]

        self.state_dict = {
            'wte': matrix(vocab_size, n_embd),
            'wpe': matrix(block_size, n_embd),
            'lm_head': matrix(vocab_size, n_embd)
        }
        for i in range(n_layer):
            self.state_dict[f'layer{i}.attn_wq'] = matrix(n_embd, n_embd)
            self.state_dict[f'layer{i}.attn_wk'] = matrix(n_embd, n_embd)
            self.state_dict[f'layer{i}.attn_wv'] = matrix(n_embd, n_embd)
            self.state_dict[f'layer{i}.attn_wo'] = matrix(n_embd, n_embd)
            self.state_dict[f'layer{i}.mlp_fc1'] = matrix(4 * n_embd, n_embd)
            self.state_dict[f'layer{i}.mlp_fc2'] = matrix(n_embd, 4 * n_embd)

        self.params = [p for mat in self.state_dict.values() for row in mat for p in row]

    def linear(self, x, w):
        return [sum((wi * xi for wi, xi in zip(wo, x)), Value(0)) for wo in w]

    def softmax(self, logits):
        max_val = max(val.data for val in logits)
        exps = [(val - max_val).exp() for val in logits]
        total = sum(exps, Value(1e-9))
        return [e / total for e in exps]

    def rmsnorm(self, x):
        ms = sum((xi * xi for xi in x), Value(0)) / len(x)
        scale = (ms + 1e-5) ** -0.5
        return [xi * scale for xi in x]

    def forward(self, token_id, pos_id, keys, values):
        tok_emb = self.state_dict['wte'][token_id]
        pos_emb = self.state_dict['wpe'][pos_id]
        x = [t + p for t, p in zip(tok_emb, pos_emb)]
        x = self.rmsnorm(x)

        for li in range(self.n_layer):
            x_residual = x
            x = self.rmsnorm(x)
            q = self.linear(x, self.state_dict[f'layer{li}.attn_wq'])
            k = self.linear(x, self.state_dict[f'layer{li}.attn_wk'])
            v = self.linear(x, self.state_dict[f'layer{li}.attn_wv'])
            keys[li].append(k)
            values[li].append(v)

            x_attn = []
            for h in range(self.n_head):
                hs = h * self.head_dim
                q_h = q[hs:hs+self.head_dim]
                k_h = [ki[hs:hs+self.head_dim] for ki in keys[li]]
                v_h = [vi[hs:hs+self.head_dim] for vi in values[li]]

                attn_logits = [sum((q_h[j] * k_h[t][j] for j in range(self.head_dim)), Value(0)) / self.head_dim**0.5 for t in range(len(k_h))]
                attn_weights = self.softmax(attn_logits)
                head_out = [sum((attn_weights[t] * v_h[t][j] for t in range(len(v_h))), Value(0)) for j in range(self.head_dim)]
                x_attn.extend(head_out)

            x = self.linear(x_attn, self.state_dict[f'layer{li}.attn_wo'])
            x = [a + b for a, b in zip(x, x_residual)]

            x_residual = x
            x = self.rmsnorm(x)
            x = self.linear(x, self.state_dict[f'layer{li}.mlp_fc1'])
            x = [xi.relu() for xi in x]
            x = self.linear(x, self.state_dict[f'layer{li}.mlp_fc2'])
            x = [a + b for a, b in zip(x, x_residual)]

        logits = self.linear(x, self.state_dict['lm_head'])
        return logits
