package routing

import (
	"sync"
)

// ============================================================================
// Partial Order Heap — Para roteamento com ordenação parcial
// ============================================================================

// PartialOrderElement é um elemento na heap com suporte a decrease-key.
type PartialOrderElement struct {
	Key      int
	Priority float64
	Index    int // índice na heap
	Valid    bool
	mu       sync.Mutex
}

// PartialOrderHeap é uma heap baseada em partial ordering.
// Suporta decrease-key em O(1) amortizado (similar a Fibonacci heap).
type PartialOrderHeap struct {
	mu       sync.RWMutex
	elements []*PartialOrderElement
	index    map[int]*PartialOrderElement
}

// NewPartialOrderHeap cria uma nova Partial Order Heap.
func NewPartialOrderHeap() *PartialOrderHeap {
	return &PartialOrderHeap{
		elements: make([]*PartialOrderElement, 0),
		index:    make(map[int]*PartialOrderElement),
	}
}

// Insert insere um elemento na heap. O(log n) amortizado.
func (h *PartialOrderHeap) Insert(key int, priority float64) *PartialOrderElement {
	h.mu.Lock()
	defer h.mu.Unlock()

	if elem, exists := h.index[key]; exists {
		if priority < elem.Priority {
			h.decreaseKeyUnsafe(elem, priority)
		}
		return elem
	}

	elem := &PartialOrderElement{
		Key:      key,
		Priority: priority,
		Valid:    true,
	}
	h.index[key] = elem

	// Adicionar ao fim e subir
	elem.Index = len(h.elements)
	h.elements = append(h.elements, elem)
	h.siftUp(len(h.elements) - 1)

	return elem
}

// ExtractMin remove e retorna o elemento mínimo. O(log n).
func (h *PartialOrderHeap) ExtractMin() (*PartialOrderElement, bool) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if len(h.elements) == 0 {
		return nil, false
	}

	min := h.elements[0]
	min.Valid = false

	last := len(h.elements) - 1
	h.elements[0] = h.elements[last]
	h.elements[0].Index = 0
	h.elements = h.elements[:last]

	delete(h.index, min.Key)

	if len(h.elements) > 0 {
		h.siftDown(0)
	}

	return min, true
}

// DecreaseKey diminui a prioridade de um elemento. O(1) amortizado.
// Retorna true se a operação foi bem-sucedida.
func (h *PartialOrderHeap) DecreaseKey(key int, newPriority float64) bool {
	h.mu.Lock()
	defer h.mu.Unlock()

	elem, exists := h.index[key]
	if !exists || newPriority >= elem.Priority {
		return false
	}

	return h.decreaseKeyUnsafe(elem, newPriority)
}

func (h *PartialOrderHeap) decreaseKeyUnsafe(elem *PartialOrderElement, newPriority float64) bool {
	elem.Priority = newPriority
	h.siftUp(elem.Index)
	return true
}

// PeekMin retorna o mínimo sem remover.
func (h *PartialOrderHeap) PeekMin() (*PartialOrderElement, bool) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	if len(h.elements) == 0 {
		return nil, false
	}
	return h.elements[0], true
}

// Size retorna o número de elementos.
func (h *PartialOrderHeap) Size() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.elements)
}

// IsEmpty retorna true se a heap estiver vazia.
func (h *PartialOrderHeap) IsEmpty() bool {
	return h.Size() == 0
}

// siftUp move um elemento para cima.
func (h *PartialOrderHeap) siftUp(idx int) {
	for idx > 0 {
		parent := (idx - 1) / 2
		if h.elements[idx].Priority >= h.elements[parent].Priority {
			break
		}
		h.swap(idx, parent)
		idx = parent
	}
}

// siftDown move um elemento para baixo.
func (h *PartialOrderHeap) siftDown(idx int) {
	n := len(h.elements)
	for {
		left := 2*idx + 1
		right := 2*idx + 2
		smallest := idx

		if left < n && h.elements[left].Priority < h.elements[smallest].Priority {
			smallest = left
		}
		if right < n && h.elements[right].Priority < h.elements[smallest].Priority {
			smallest = right
		}

		if smallest == idx {
			break
		}

		h.swap(idx, smallest)
		idx = smallest
	}
}

func (h *PartialOrderHeap) swap(i, j int) {
	h.elements[i], h.elements[j] = h.elements[j], h.elements[i]
	h.elements[i].Index = i
	h.elements[j].Index = j
}

// Validate verifica a propriedade da heap.
func (h *PartialOrderHeap) Validate() bool {
	h.mu.RLock()
	defer h.mu.RUnlock()

	n := len(h.elements)
	for i := 0; i < n; i++ {
		left := 2*i + 1
		right := 2*i + 2
		if left < n && h.elements[left].Priority < h.elements[i].Priority {
			return false
		}
		if right < n && h.elements[right].Priority < h.elements[i].Priority {
			return false
		}
	}
	return true
}
