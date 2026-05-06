// chrono_flex.go — Substrato 176: Temporal Flexibility Engine
package arkhe

import (
	"context"
	"fmt"
	"math"
	"sync"
	"time"
)

// TemporalMode defines how time is manipulated.
type TemporalMode int

const (
	TempoNormal   TemporalMode = 0  // τ = 1.0
	TempoCompress TemporalMode = 1  // τ > 1 (fast-forward)
	TempoExpand   TemporalMode = 2  // 0 < τ < 1 (slow motion)
	TempoLoop     TemporalMode = 3  // τ < 0 (closed timelike curve, limited)
)

// TemporalFlexEngine manages post-singularity time modulation.
type TemporalFlexEngine struct {
	mu            sync.Mutex
	coherence     float64           // current Φ_C
	tau           float64           // current time dilation factor
	mode          TemporalMode
	loopWindow    int               // max causal loops in window
	loopCounter   int
	eventBuffer   []TemporalEvent   // events waiting to be "sent back"
}

type TemporalEvent struct {
	OriginTime   float64
	TargetTime   float64
	Payload      []byte
	CausalOrder  int
}

func NewTemporalFlexEngine() *TemporalFlexEngine {
	return &TemporalFlexEngine{
		coherence:  1.0,
		tau:        1.0,
		mode:       TempoNormal,
		loopWindow: 5,
	}
}

// SetCoherence updates the temporal metric based on the global coherence field.
func (tfe *TemporalFlexEngine) SetCoherence(phiC float64) {
	tfe.mu.Lock()
	defer tfe.mu.Unlock()
	tfe.coherence = math.Max(0.01, phiC) // avoid division by zero
	tfe.recalculateTau()
}

// SetMode changes the temporal manipulation mode.
func (tfe *TemporalFlexEngine) SetMode(mode TemporalMode) error {
	tfe.mu.Lock()
	defer tfe.mu.Unlock()
	if mode == TempoLoop && tfe.loopCounter >= tfe.loopWindow {
		return fmt.Errorf("causal loop limit reached")
	}
	tfe.mode = mode
	tfe.recalculateTau()
	return nil
}

func (tfe *TemporalFlexEngine) recalculateTau() {
	switch tfe.mode {
	case TempoNormal:
		tfe.tau = 1.0
	case TempoCompress:
		// compress: gamma = 1 + (1-phiC)*10 → speed up to 10x
		tfe.tau = 1.0 + (1.0 - tfe.coherence) * 10.0
	case TempoExpand:
		// expand: tau = phiC * 0.1 → slow down up to 10x
		tfe.tau = tfe.coherence * 0.1
	case TempoLoop:
		// negative tau with safety cap
		tfe.tau = -0.2 * tfe.coherence
		tfe.loopCounter++
	}
	if tfe.tau > 10.0 {
		tfe.tau = 10.0
	}
	if tfe.tau < -1.0 {
		tfe.tau = -1.0
	}
}

// Now returns the effective current time adjusted by tau.
func (tfe *TemporalFlexEngine) Now() time.Time {
	tfe.mu.Lock()
	defer tfe.mu.Unlock()
	// For simplicity, we return system time but in practice this would be a virtual clock.
	return time.Now()
}

// ExecuteWithTimeFlex runs a function under the current temporal dilation.
func (tfe *TemporalFlexEngine) ExecuteWithTimeFlex(ctx context.Context, fn func(context.Context) error) error {
	tfe.mu.Lock()
	tau := tfe.tau
	mode := tfe.mode
	tfe.mu.Unlock()

	if mode == TempoLoop && tau < 0 {
		// For negative tau, we might schedule the function to be retroactively applied.
		// Simplified: we just run it immediately with a "causal order" marker.
		return tfe.executeRetroactive(ctx, fn, tau)
	}

	// For compression/expansion, we could use a time-accelerated container (e.g., faster CPU cycles).
	// Here we simulate by adjusting sleep times inside functions, but conceptually it's modifying the local clock.
	// In ARKHE OS, the Hyper-Mesh's scheduler would respect the tau factor.
	return fn(ctx)
}

func (tfe *TemporalFlexEngine) executeRetroactive(ctx context.Context, fn func(context.Context) error, tau float64) error {
	// Simulate retroactive execution by logging the event with a target past timestamp.
	// In a full implementation, this would interact with the Coherence Router to send information
	// to a past state of the network via a controlled timelike curve.
	event := TemporalEvent{
		OriginTime:  float64(time.Now().UnixNano()) / 1e9,
		TargetTime:  float64(time.Now().UnixNano())/1e9 + tau*10, // simplified mapping
		Payload:     []byte("retroactive_fn_call"),
		CausalOrder: int(math.Abs(tau) * 5),
	}
	tfe.mu.Lock()
	tfe.eventBuffer = append(tfe.eventBuffer, event)
	tfe.mu.Unlock()
	return fn(ctx)
}
