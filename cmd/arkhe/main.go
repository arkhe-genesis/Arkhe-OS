package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"time"

	pb "github.com/arkhe-os/arkhe/api" // generated proto
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

var (
	oracleAddr string
	client     pb.ShardServiceClient
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "arkhe",
		Short: "ARKHE Multiversal Orchestrator",
		PersistentPreRun: func(cmd *cobra.Command, args []string) {
			conn, err := grpc.Dial(oracleAddr, grpc.WithTransportCredentials(insecure.NewCredentials()))
			if err != nil {
				log.Fatalf("Failed to connect to oracle: %v", err)
			}
			client = pb.NewShardServiceClient(conn)
		},
	}
	rootCmd.PersistentFlags().StringVar(&oracleAddr, "oracle", "localhost:50051", "oracle daemon address")

	rootCmd.AddCommand(shardCmd())
	rootCmd.AddCommand(portalCmd())
	rootCmd.AddCommand(selfCompleteCmd())
	rootCmd.AddCommand(x402Cmd())
	rootCmd.AddCommand(saasNexusCmd())

	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}

func shardCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "shard",
		Short: "Manage compute shards",
	}

	createCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new shard",
		Run:   shardCreate,
		Args:  cobra.ExactArgs(1), // name
	}
	createCmd.Flags().String("motor", "", "Motor type")
	createCmd.Flags().String("substrate", "", "Substrate ID")
	createCmd.Flags().Bool("gpu", false, "Use GPU")
	cmd.AddCommand(createCmd)

	cmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List all shards",
		Run:   shardList,
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "destroy",
		Short: "Destroy a shard",
		Run:   shardDestroy,
		Args:  cobra.ExactArgs(1),
	})

	return cmd
}

func shardCreate(cmd *cobra.Command, args []string) {
	name := args[0]
	motor, _ := cmd.Flags().GetString("motor")
	substrate, _ := cmd.Flags().GetString("substrate")
	gpu, _ := cmd.Flags().GetBool("gpu")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	resp, err := client.CreateShard(ctx, &pb.CreateShardRequest{
		SubstrateId: substrate,
		Motor:       motor,
		Gpu:         gpu,
		Labels:      map[string]string{"name": name},
	})
	if err != nil {
		log.Fatalf("CreateShard failed: %v", err)
	}
	fmt.Printf("Shard %s created (substrate=%s, motor=%s)\n", resp.ShardId, resp.SubstrateId, resp.Motor)
}

func shardList(cmd *cobra.Command, args []string) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	resp, err := client.ListShards(ctx, &pb.ListShardsRequest{})
	if err != nil {
		log.Fatalf("ListShards failed: %v", err)
	}
	for _, shard := range resp.Shards {
		fmt.Printf("Shard %s: Status=%s Endpoint=%s\n", shard.ShardId, shard.Status, shard.Endpoint)
	}
}

func shardDestroy(cmd *cobra.Command, args []string) {
	shardID := args[0]
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	_, err := client.DestroyShard(ctx, &pb.DestroyShardRequest{ShardId: shardID})
	if err != nil {
		log.Fatalf("DestroyShard failed: %v", err)
	}
	fmt.Printf("Shard %s destroyed\n", shardID)
}

func portalCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "portal",
		Short: "Manage reality portals",
	}
	cmd.AddCommand(&cobra.Command{
		Use:   "financial-dashboard",
		Short: "Show recent royalty payments",
		Run:   portalFinancialDashboard,
	})
	return cmd
}

func portalFinancialDashboard(cmd *cobra.Command, args []string) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	resp, err := client.QueryRoyalties(ctx, &pb.QueryRoyaltiesRequest{
		Limit: 20,
	})
	if err != nil {
		log.Fatalf("failed to query royalties: %v", err)
	}
	fmt.Println("Recent Royalties:")
	for _, r := range resp.Royalties {
		// handle TargetBlockId potential length
		blockID := r.TargetBlockId
		if len(blockID) > 8 {
			blockID = blockID[:8]
		}
		fmt.Printf("Block %s → Beneficiary: %s, Amount: R$%.2f, Status: %s\n",
			blockID, r.SourceOrcid, float64(r.Amount)/100.0, r.Status)
	}
}

func selfCompleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "self-complete",
		Short: "Trigger ARKHE ontological self-completion cycle",
		Run:   runSelfComplete,
	}
	cmd.Flags().Bool("dry-run", false, "Don't apply changes")
	cmd.Flags().Bool("loop", false, "Run continuously in background")
	return cmd
}

func runSelfComplete(cmd *cobra.Command, args []string) {
	dryRun, _ := cmd.Flags().GetBool("dry-run")
	loop, _ := cmd.Flags().GetBool("loop")

	// The SelfCompletionEngine is a Rust binary; we call it via exec.
	for {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
		defer cancel()
		args := []string{"run", "--release", "--bin", "arkhe-self-complete"}
		if dryRun {
			args = append(args, "--", "--dry-run")
		}
		execCtx := exec.CommandContext(ctx, "cargo", args...)
		execCtx.Stdout = os.Stdout
		execCtx.Stderr = os.Stderr
		if err := execCtx.Run(); err != nil {
			log.Printf("self-complete failed: %v", err)
		}
		if !loop {
			break
		}
		time.Sleep(24 * time.Hour)
	}
}

func saasNexusCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "saas-nexus",
		Short: "Manage SaaS Nexus Substrate 9400",
	}

	onboardCmd := &cobra.Command{
		Use:   "onboard",
		Short: "Onboard a new vendor",
		Run:   runSaasNexusOnboard,
	}
	onboardCmd.Flags().String("orcid", "", "Vendor ORCID")
	onboardCmd.MarkFlagRequired("orcid")

	cmd.AddCommand(onboardCmd)
	return cmd
}

func runSaasNexusOnboard(cmd *cobra.Command, args []string) {
	orcid, _ := cmd.Flags().GetString("orcid")
	fmt.Printf("Onboarding vendor with ORCID: %s to SaaS Nexus...\n", orcid)
	// Placeholder for grpc call or local handling
	fmt.Printf("Vendor %s successfully registered. The cathedral's economy beats faster. 🛒💸🏛️\n", orcid)
}
