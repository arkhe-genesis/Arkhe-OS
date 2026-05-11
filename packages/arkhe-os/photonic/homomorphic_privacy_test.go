package photonic

import (
	"testing"
)

func TestCompositionalFHEEngine(t *testing.T) {
	config := CompositionalFHEConfig{
		SecurityLevel:     128,
		NoiseBudget:       0.1,
		CompositionRounds: 5,
	}
	engine := NewCompositionalFHEEngine(config)

	originalState := &CompressedAPIState{
		StateID: "test_state",
		CompressedState: []complex128{
			complex(1.0, 0),
			complex(0.5, 0.5),
		},
		PhotonicCoherence: 0.95,
	}

	encrypted, err := engine.EncryptCompressedState(originalState)
	if err != nil {
		t.Fatalf("Encryption failed: %v", err)
	}

	if len(encrypted.EncryptedData) != len(originalState.CompressedState) {
		t.Fatalf("Encrypted data length mismatch")
	}

	decrypted, err := engine.DecryptCompressedState(encrypted)
	if err != nil {
		t.Fatalf("Decryption failed: %v", err)
	}

	if decrypted.StateID != originalState.StateID {
		t.Fatalf("State ID mismatch after decryption")
	}

	if decrypted.PhotonicCoherence != originalState.PhotonicCoherence {
		t.Fatalf("Photonic coherence mismatch after decryption")
	}

    // We used a mock scaling factor for FHE logic in the file: * complex(0.99, 0.01)
    // Then decrypted with / complex(0.99, 0.01)
    // Values should match closely
}
