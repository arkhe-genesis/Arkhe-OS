package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/spf13/cobra"
)

func x402Cmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "x402",
		Short: "Manage x402 Web3 integrations (e.g. 0xArchive API)",
	}

	subscribeCmd := &cobra.Command{
		Use:   "subscribe",
		Short: "Subscribe to a paid tier via x402 USDC payment",
		Run:   runX402Subscribe,
	}
	subscribeCmd.Flags().String("tier", "Build", "Subscription tier (Build or Pro)")
	subscribeCmd.Flags().String("payment-signature", "", "EIP-3009 signed transfer for x402 billing")

	cmd.AddCommand(subscribeCmd)
	return cmd
}

func runX402Subscribe(cmd *cobra.Command, args []string) {
	tier, _ := cmd.Flags().GetString("tier")
	signature, _ := cmd.Flags().GetString("payment-signature")

	if signature == "" {
		fmt.Println("Error: --payment-signature is required for x402 subscription.")
		return
	}

	fmt.Printf("Subscribing to %s tier via 0xArchive x402 payment flow...\n", tier)

	payload := map[string]string{
		"tier": tier,
	}
	jsonData, _ := json.Marshal(payload)

	req, err := http.NewRequestWithContext(
		context.Background(),
		"POST",
		"https://api.0xarchive.io/v1/web3/subscribe",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		fmt.Printf("Failed to create request: %v\n", err)
		return
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("payment-signature", signature)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("Failed to execute request: %v\n", err)
		return
	}
	defer resp.Body.Close()

	bodyBytes, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		fmt.Println("Subscription successful!")
		fmt.Printf("Response: %s\n", string(bodyBytes))
	} else {
		fmt.Printf("Subscription failed. Status: %s\n", resp.Status)
		fmt.Printf("Response: %s\n", string(bodyBytes))
	}
}
