package main

import (
	"fmt"
	"log"
	"arkhe/packaging"
)

func main() {
    config := packaging.PublisherConfig{
        EnableOctraVerification: true,
        PublishToPyPI:           true,
        PublishToCargo:          true,
        PublishToGoModules:      true,
        PublishToNPM:            true,
        OctraNodeURL:            "https://node.octra.network",
    }

    publisher := packaging.NewFederatedPublisher("pub_001", config)

    fmt.Println("🚀 Starting Federated Publishing of Arkhe OS Substrates 0-230...")

    record, err := publisher.Publish("v0.0.230", ".")
    if err != nil {
        log.Fatalf("❌ Publishing failed: %v", err)
    }

    if record.Success {
        fmt.Println("✅ Publishing successful!")
        fmt.Printf("📦 Version: %s\n", record.Version)
        fmt.Printf("🌐 Platforms: %v\n", record.Platforms)
        fmt.Printf("⛓️  Octra Tx: %s\n", record.OctraTxHash)
    } else {
        fmt.Println("⚠️ Publishing completed with errors or no platforms targeted.")
    }
}
