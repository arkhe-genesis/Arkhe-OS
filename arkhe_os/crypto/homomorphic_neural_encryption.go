package crypto

import (
	"crypto/rand"
	"fmt"
	"math/big"
	"sync"
)

// O objetivo disto é proteger os gradientes durante agregação federada
// Usando esquemas de Fully Homomorphic Encryption (FHE) adaptados

// Ciphertext representa um gradiente cifrado
type Ciphertext struct {
	C0 *big.Int
	C1 *big.Int
}

// HomomorphicEncryptionEngine gerencia cifragem FHE
type HomomorphicEncryptionEngine struct {
	mu sync.RWMutex
	// Parâmetros simplificados de chave pública/privada para BFV/CKKS
	P *big.Int // Modulus grande
	Q *big.Int // Modulus do ciphertext
}

func NewHomomorphicEncryptionEngine() *HomomorphicEncryptionEngine {
	// Inicialização básica com primos grandes para simulação
	p, _ := rand.Prime(rand.Reader, 128)
	q, _ := rand.Prime(rand.Reader, 256)

	return &HomomorphicEncryptionEngine{
		P: p,
		Q: q,
	}
}

// EncryptGradient cifra um vetor de gradiente (representado como float64, mas convertido p/ inteiros fixos internamente)
func (h *HomomorphicEncryptionEngine) EncryptGradient(gradient []float64) ([]*Ciphertext, error) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	ciphertexts := make([]*Ciphertext, len(gradient))

	// Simulação de cifragem FHE
	for i, val := range gradient {
		// Multiplicar por fator de escala para simular CKKS (ponto flutuante -> inteiro)
		scaled := int64(val * 1e6)
		m := big.NewInt(scaled)

		// rAleatório
		r, _ := rand.Int(rand.Reader, h.Q)

		// C0 = (P * r + m) mod Q (Simplificação extrema para demonstração)
		c0 := new(big.Int).Mul(h.P, r)
		c0.Add(c0, m)
		c0.Mod(c0, h.Q)

		c1, _ := rand.Int(rand.Reader, h.Q)

		ciphertexts[i] = &Ciphertext{C0: c0, C1: c1}
	}

	return ciphertexts, nil
}

// AggregateEncryptedGradients soma gradientes cifrados sem decifrá-los
func (h *HomomorphicEncryptionEngine) AggregateEncryptedGradients(g1, g2 []*Ciphertext) ([]*Ciphertext, error) {
	if len(g1) != len(g2) {
		return nil, fmt.Errorf("gradientes devem ter o mesmo tamanho")
	}

	h.mu.RLock()
	defer h.mu.RUnlock()

	result := make([]*Ciphertext, len(g1))

	for i := range g1 {
		c0 := new(big.Int).Add(g1[i].C0, g2[i].C0)
		c0.Mod(c0, h.Q)

		c1 := new(big.Int).Add(g1[i].C1, g2[i].C1)
		c1.Mod(c1, h.Q)

		result[i] = &Ciphertext{C0: c0, C1: c1}
	}

	return result, nil
}

// DecryptGradient decifra o resultado final (requer chave privada)
func (h *HomomorphicEncryptionEngine) DecryptGradient(ciphertexts []*Ciphertext) ([]float64, error) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	result := make([]float64, len(ciphertexts))

	for i, c := range ciphertexts {
		// m = (C0 mod P)
		m := new(big.Int).Mod(c.C0, h.P)

		// Lidar com números negativos simulados
		halfP := new(big.Int).Div(h.P, big.NewInt(2))
		if m.Cmp(halfP) > 0 {
			m.Sub(m, h.P)
		}

		result[i] = float64(m.Int64()) / 1e6
	}

	return result, nil
}
