# Mathematical Foundations of Deep Learning & Transformers

This document provides a mathematical breakdown of several fundamental concepts used in modern deep learning and large language models (LLMs).

## 1. Math Behind Attention - Q, K, and V

In the self-attention mechanism of Transformers, each token in the input sequence is mapped to three distinct vectors: a **Query (Q)**, a **Key (K)**, and a **Value (V)**. This is achieved by multiplying the input embedding matrix $X$ (of shape $N \times d_{\text{model}}$) by learned weight matrices:

*   $Q = X W_Q$
*   $K = X W_K$
*   $V = X W_V$

Here, $W_Q, W_K \in \mathbb{R}^{d_{\text{model}} \times d_k}$ and $W_V \in \mathbb{R}^{d_{\text{model}} \times d_v}$.

The core idea is to compute a set of attention weights that determine how much focus each query should place on every key. This is calculated using the dot product between $Q$ and $K$. The final attention output is a weighted sum of the values $V$:

$$ \text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V $$

*   $QK^T$ computes the unnormalized similarity (or attention score) between all queries and keys. The resulting matrix has shape $N \times N$.
*   The `softmax` function is applied row-wise to convert these raw scores into probabilities that sum to 1.
*   Finally, multiplying by $V$ produces the output representation, where each token incorporates information from the entire sequence based on the attention weights.

## 2. Math Behind $\sqrt{d_k}$ Scaling Factor in Attention

The dot product attention formula includes a division by $\sqrt{d_k}$, where $d_k$ is the dimensionality of the keys (and queries). This is known as **Scaled Dot-Product Attention**.

**Why is this necessary?**
Assume that the components of $Q$ and $K$ are independent random variables with a mean of 0 and a variance of 1 ($\mu = 0, \sigma^2 = 1$).

The dot product of a single query vector $q$ and key vector $k$ is $q \cdot k = \sum_{i=1}^{d_k} q_i k_i$.
Because $q_i$ and $k_i$ are independent with variance 1, the variance of their product $q_i k_i$ is also 1.
Therefore, the variance of the sum of $d_k$ such terms is:

$$ \text{Var}(q \cdot k) = \sum_{i=1}^{d_k} \text{Var}(q_i k_i) = d_k $$

This means that as $d_k$ grows, the dot product values grow in magnitude. Large positive or negative values passed into the `softmax` function cause it to be pushed into regions where its gradient is extremely small (the "vanishing gradient" problem). This makes learning very slow or stops it entirely.

By dividing the dot product by $\sqrt{d_k}$, the variance is scaled down to 1:

$$ \text{Var}\left(\frac{q \cdot k}{\sqrt{d_k}}\right) = \frac{1}{(\sqrt{d_k})^2} \text{Var}(q \cdot k) = \frac{1}{d_k} \cdot d_k = 1 $$

This ensures the arguments to the `softmax` remain relatively small, keeping the gradients stable and facilitating effective backpropagation.

## 3. Math Behind Backpropagation

Backpropagation is an algorithm used to calculate the gradient of the loss function with respect to the network's weights. It heavily relies on the **Chain Rule** from calculus.

Let's consider a simple neural network layer with weight $w$, input $x$, linear transformation $z = w \cdot x$, activation function $a = f(z)$, and loss $L$. We want to find how a small change in $w$ affects $L$, which is the partial derivative $\frac{\partial L}{\partial w}$.

Using the chain rule, we can break this down backwards from the output:

$$ \frac{\partial L}{\partial w} = \frac{\partial L}{\partial a} \cdot \frac{\partial a}{\partial z} \cdot \frac{\partial z}{\partial w} $$

1.  **$\frac{\partial L}{\partial a}$**: How the loss changes with respect to the activation output.
2.  **$\frac{\partial a}{\partial z} = f'(z)$**: The derivative of the activation function.
3.  **$\frac{\partial z}{\partial w} = x$**: Since $z = wx$, the derivative with respect to $w$ is simply the input $x$.

For a deep network, this process is computed iteratively from the final layer back to the first layer, reusing the gradients computed for the later layers to calculate the gradients for the earlier layers.

## 4. Math Behind Gradient Descent

Gradient descent is the optimization algorithm used to minimize the loss function $L(w)$ by iteratively updating the weights $w$.

The gradient $\nabla L(w)$ represents the direction of the steepest ascent (where the loss increases fastest). To minimize the loss, we must move in the opposite direction.

The weight update rule is:

$$ w_{\text{new}} = w_{\text{old}} - \alpha \nabla L(w_{\text{old}}) $$

Where:
*   $w$: The weights (parameters) of the model.
*   $\nabla L(w)$: The gradient of the loss function with respect to $w$.
*   $\alpha$: The **learning rate**, a small positive scalar that determines the step size taken in the direction of the negative gradient.

By repeatedly applying this update, the weights gradually converge towards a local or global minimum of the loss function space.

## 5. Math Behind Cross-Entropy Loss

Cross-Entropy (CE) loss is the standard loss function for classification problems. It measures the difference between two probability distributions: the true distribution $y$ (typically a one-hot encoded vector representing the true label) and the predicted distribution $\hat{y}$ (the output of a softmax layer).

For a single data point with $C$ classes, the cross-entropy loss is defined as:

$$ H(y, \hat{y}) = - \sum_{i=1}^{C} y_i \log(\hat{y}_i) $$

Where:
*   $y_i$ is the true probability of class $i$ (1 for the correct class, 0 for others in one-hot encoding).
*   $\hat{y}_i$ is the predicted probability of class $i$.

Because $y$ is typically one-hot encoded, only the term corresponding to the true class (let's say class $c$) is non-zero. The formula simplifies to:

$$ H(y, \hat{y}) = - \log(\hat{y}_c) $$

This means the loss only cares about the predicted probability for the correct class. If $\hat{y}_c$ approaches 1, $\log(1) = 0$, and the loss is zero. If $\hat{y}_c$ is close to 0, $\log(\hat{y}_c)$ becomes a large negative number, resulting in a very high loss. This heavily penalizes the model for being confident in the wrong answer.

## 6. Math Behind RoPE (Rotary Position Embedding)

Traditional Transformers use absolute or relative positional embeddings added to the input tokens. **Rotary Position Embedding (RoPE)** (introduced in the RoFormer paper) encodes positional information directly into the attention mechanism by rotating the query and key vectors in a multi-dimensional complex plane.

For a query or key vector $x \in \mathbb{R}^d$, we treat consecutive pairs of elements as complex numbers: $(x_1, x_2) \rightarrow x_1 + ix_2$.
To encode position $m$, we multiply the complex numbers by $e^{i m \theta_j}$, which represents a rotation by angle $m \theta_j$ in the 2D plane.
The angles $\theta_j$ are predefined constants (usually $\theta_j = 10000^{-2j/d}$).

In real numbers, this is equivalent to applying a rotation matrix $R_{\Theta, m}^d$ to the vector:

$$ f(x, m) = R_{\Theta, m}^d x $$

Where the rotation matrix consists of $2 \times 2$ block diagonal matrices:

$$ R_{\Theta, m}^d = \begin{pmatrix}
\cos(m\theta_1) & -\sin(m\theta_1) & 0 & 0 & \dots \\
\sin(m\theta_1) & \cos(m\theta_1) & 0 & 0 & \dots \\
0 & 0 & \cos(m\theta_2) & -\sin(m\theta_2) & \dots \\
0 & 0 & \sin(m\theta_2) & \cos(m\theta_2) & \dots \\
\vdots & \vdots & \vdots & \vdots & \ddots
\end{pmatrix} $$

**Why is this powerful?**
When calculating attention, we compute the dot product between a query at position $m$ and a key at position $n$: $q_m \cdot k_n$.
Because the inner product of two rotated vectors depends only on the relative angle between them, RoPE mathematically ensures that:

$$ (R_{\Theta, m}^d W_Q x_m)^T (R_{\Theta, n}^d W_K x_n) = (W_Q x_m)^T R_{\Theta, n-m}^d (W_K x_n) $$

Thus, the dot product natively incorporates the **relative position ($n-m$)** between the tokens, even though we only applied an absolute rotation to each token individually.

## 7. Math Behind RMSNorm (Root Mean Square Layer Normalization)

RMSNorm is a computationally efficient variant of Layer Normalization. Standard LayerNorm normalizes the input vector $a \in \mathbb{R}^d$ using both the mean $\mu$ and the variance $\sigma^2$:

$$ \text{LayerNorm}(a) = \frac{a - \mu}{\sqrt{\sigma^2 + \epsilon}} \odot g + b $$

Research showed that the *mean-centering* operation (subtracting $\mu$) is largely unnecessary for model performance, and that the scaling invariance provided by the variance normalization is the primary factor for success.

RMSNorm drops the mean calculation entirely. Instead of variance, it calculates the **Root Mean Square (RMS)** of the activations:

$$ \text{RMS}(a) = \sqrt{\frac{1}{d} \sum_{i=1}^{d} a_i^2 + \epsilon} $$

The input vector is then divided by the RMS and scaled by a learned parameter $g_i$:

$$ \text{RMSNorm}(a_i) = \frac{a_i}{\text{RMS}(a)} \cdot g_i $$

By removing the need to compute the mean and subtract it from every element, RMSNorm is mathematically simpler, requires fewer operations, and typically executes 10% to 50% faster than standard LayerNorm without degrading model accuracy.
