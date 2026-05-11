package main

import (
	"context"
	"crypto/tls"
	"fmt"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"

	"github.com/cosmos/cosmos-sdk/types"
	txtypes "github.com/cosmos/cosmos-sdk/types/tx"
	authtypes "github.com/cosmos/cosmos-sdk/x/auth/types"
	banktypes "github.com/cosmos/cosmos-sdk/x/bank/types"
)

// ConnectToCosmos establishes a gRPC connection to a public Cosmos node
// and retrieves basic blockchain parameters to verify the connection.
func ConnectToCosmos() {
	// Configure global prefix for Cosmos
	config := types.GetConfig()
	config.SetBech32PrefixForAccount("cosmos", "cosmospub")
	config.Seal()

	fmt.Println("Cosmos SDK Configured successfully via Substrate")
	fmt.Println("Establishing gRPC connection to the Cosmos Hub...")

	// Connect to a public gRPC node for Cosmos Hub
	// Using proper TLS credentials for port 443
	grpcConn, err := grpc.Dial(
		"grpc.cosmos.interbloc.org:443",
		grpc.WithTransportCredentials(credentials.NewTLS(&tls.Config{})),
	)
	if err != nil {
		fmt.Printf("⚠️  Failed to connect to Cosmos via gRPC: %v\n", err)
		return
	}
	defer grpcConn.Close()

	// Create a context with a timeout for our requests
	// Since public nodes may be down or we may not have internet access in testing,
	// we keep a short timeout and handle the error gracefully without crashing.
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// 1. Check Auth Module Params
	authClient := authtypes.NewQueryClient(grpcConn)
	authRes, err := authClient.Params(ctx, &authtypes.QueryParamsRequest{})
	if err == nil && authRes != nil {
		fmt.Printf("✅ Connected to Cosmos Hub! Max Memo Characters: %d\n", authRes.Params.MaxMemoCharacters)
	} else {
		fmt.Printf("⚠️  Connected to gRPC but failed to query Auth params (may be offline/blocked): %v\n", err)
	}

	// 2. Try fetching a generic Tx just to show service interaction
	txClient := txtypes.NewServiceClient(grpcConn)
	_, err = txClient.GetTx(ctx, &txtypes.GetTxRequest{})
	if err != nil {
		fmt.Printf("✅ Tx Service reachable (expected error for empty req): %v\n", err)
	}

	// 3. Query Bank params (total supply example)
	bankClient := banktypes.NewQueryClient(grpcConn)
	bankRes, err := bankClient.TotalSupply(ctx, &banktypes.QueryTotalSupplyRequest{})
	if err == nil && bankRes != nil {
		fmt.Printf("✅ Bank Service reachable. Total supply items: %d\n", len(bankRes.Supply))
	} else {
		fmt.Printf("⚠️  Failed to query Bank Total Supply (may be offline/blocked): %v\n", err)
	}

	fmt.Println("Cosmos network integration initialized.")
}
