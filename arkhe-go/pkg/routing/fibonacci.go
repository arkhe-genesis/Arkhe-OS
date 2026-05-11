package routing

import (
	"math"
	_ "unsafe"
)

// ============================================================================
// Fibonacci Heap — para o algoritmo de Dijkstra
// ============================================================================

// fibNode é um nó na Fibonacci heap.
type fibNode struct {
	key      int     // identificador do vértice
	value    float64 // valor da chave (distância)
	parent   *fibNode
	child    *fibNode
	left     *fibNode
	right    *fibNode
	degree   int
	mark     bool
	expired  bool  // true se o nó expirou (TTL)
}

// FibonacciHeap é uma Fibonacci heap mínima.
type FibonacciHeap struct {
	min    *fibNode
	nodes  map[int]*fibNode // mapeia key → nó
	count  int
}

// NewFibonacciHeap cria uma nova Fibonacci heap vazia.
func NewFibonacciHeap() *FibonacciHeap {
	return &FibonacciHeap{
		nodes: make(map[int]*fibNode),
	}
}

// IsEmpty retorna true se a heap estiver vazia.
func (h *FibonacciHeap) IsEmpty() bool {
	return h.min == nil
}

// Insert insere um novo nó na heap. O(1) amortizado.
func (h *FibonacciHeap) Insert(key int, value float64, expired bool) *fibNode {
	node := &fibNode{
		key:     key,
		value:   value,
		expired: expired,
	}

	// Inserir na lista circular de raízes
	if h.min == nil {
		node.left = node
		node.right = node
		h.min = node
	} else {
		h.insertRoot(node)
		if value < h.min.value {
			h.min = node
		}
	}

	h.nodes[key] = node
	h.count++

	return node
}

// DecreaseKey diminui o valor de um nó. O(1) amortizado.
func (h *FibonacciHeap) DecreaseKey(node *fibNode, newValue float64) {
	if newValue > node.value {
		return // não é decrease
	}

	node.value = newValue
	parent := node.parent

	if parent != nil && node.value < parent.value {
		h.cut(node, parent)
		h.cascadingCut(parent)
	}

	if node.value < h.min.value {
		h.min = node
	}
}

// DecreaseKeyOrInsert diminui a chave se o nó existir, ou insere se não existir.
func (h *FibonacciHeap) DecreaseKeyOrInsert(key int, value float64, expired bool) {
	if node, exists := h.nodes[key]; exists {
		if value < node.value {
			h.DecreaseKey(node, value)
		}
		return
	}
	h.Insert(key, value, expired)
}

// ExtractMin remove e retorna o nó mínimo. O(log n) amortizado.
func (h *FibonacciHeap) ExtractMin() (int, float64, bool) {
	if h.min == nil {
		return -1, math.Inf(1), false
	}

	minNode := h.min
	z := minNode

	// Adicionar filhos à lista de raízes
	if z.child != nil {
		child := z.child
		for {
			next := child.right
			h.insertRoot(child)
			child.parent = nil
			child = next
			if child == z.child {
				break
			}
		}
	}

	// Remover z da lista de raízes
	h.removeRoot(z)
	delete(h.nodes, z.key)

	if z == z.right {
		h.min = nil
	} else {
		h.min = z.right
		h.consolidate()
	}

	h.count--

	expired := z.expired
	return z.key, z.value, expired
}

// consolidate consolida as árvores de mesmo grau.
func (h *FibonacciHeap) consolidate() {
	maxDegree := int(math.Log2(float64(h.count))) + 1
	if maxDegree < 1 {
		maxDegree = 1
	}

	A := make([]*fibNode, maxDegree+1)

	// Iterar sobre raízes
	roots := h.collectRoots()
	for _, w := range roots {
		x := w
		d := x.degree

		for d < len(A) && A[d] != nil {
			y := A[d]
			if x.value > y.value {
				x, y = y, x
			}
			h.link(y, x)
			A[d] = nil
			d++
		}

		if d < len(A) {
			A[d] = x
		}
	}

	// Encontrar novo mínimo
	h.min = nil
	for _, node := range A {
		if node != nil {
			if h.min == nil {
				h.min = node
				node.left = node
				node.right = node
			} else {
				h.insertRoot(node)
				if node.value < h.min.value {
					h.min = node
				}
			}
		}
	}
}

// link torna y filho de x.
func (h *FibonacciHeap) link(y, x *fibNode) {
	h.removeRoot(y)
	y.left = y
	y.right = y
	y.parent = x

	if x.child == nil {
		x.child = y
	} else {
		h.insertRootList(x.child, y)
	}

	x.degree++
	y.mark = false
}

func (h *FibonacciHeap) cut(node, parent *fibNode) {
	// Remover node da lista de filhos
	if node.right == node {
		parent.child = nil
	} else {
		if parent.child == node {
			parent.child = node.right
		}
		node.right.left = node.left
		node.left.right = node.right
	}
	parent.degree--

	// Adicionar node à lista de raízes
	h.insertRoot(node)
	node.parent = nil
	node.mark = false
}

func (h *FibonacciHeap) cascadingCut(node *fibNode) {
	parent := node.parent
	if parent != nil {
		if !node.mark {
			node.mark = true
		} else {
			h.cut(node, parent)
			h.cascadingCut(parent)
		}
	}
}

// Helpers

func (h *FibonacciHeap) insertRoot(node *fibNode) {
	if h.min == nil {
		node.left = node
		node.right = node
		return
	}
	h.insertRootList(h.min, node)
}

func (h *FibonacciHeap) insertRootList(root, node *fibNode) {
	node.right = root.right
	node.left = root
	root.right.left = node
	root.right = node
}

func (h *FibonacciHeap) removeRoot(node *fibNode) {
	if node.right == node {
		return
	}
	node.left.right = node.right
	node.right.left = node.left
}

func (h *FibonacciHeap) collectRoots() []*fibNode {
	var roots []*fibNode
	if h.min == nil {
		return roots
	}

	current := h.min
	for {
		roots = append(roots, current)
		current = current.right
		if current == h.min {
			break
		}
	}
	return roots
}

// unsafeStringToBytes converte string para []byte sem alocação extra.
// Usada em hot paths.
//go:linkname unsafeStringToBytes runtime.stringtoslicebyte
func unsafeStringToBytes(s string) []byte
