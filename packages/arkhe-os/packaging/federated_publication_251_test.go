package packaging

import (
	"testing"
)

func TestFederatedPublisher(t *testing.T) {
	publisher := NewFederatedPublisher()
	if publisher == nil {
		t.Fatal("Expected non-nil FederatedPublisher")
	}

	err := publisher.PackageSubstrates()
	if err != nil {
		t.Fatalf("Failed to package substrates: %v", err)
	}
	if publisher.IntegrityHash == "" {
		t.Fatal("Expected non-empty IntegrityHash after packaging")
	}

	err = publisher.VerifyOnOctraBlockchain()
	if err != nil {
		t.Fatalf("Failed to verify on Octra blockchain: %v", err)
	}
	if !publisher.OctraVerified {
		t.Fatal("Expected OctraVerified to be true")
	}

	results := publisher.PublishToEcosystems()
	if len(results) == 1 && results["error"] != "" {
		t.Fatalf("PublishToEcosystems failed: %v", results["error"])
	}
	if results["Hashtree"] == "" {
		t.Fatal("Expected successful push to Hashtree via Nostr")
	}
}
