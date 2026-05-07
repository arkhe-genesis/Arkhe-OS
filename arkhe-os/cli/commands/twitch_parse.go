// cli/commands/twitch_parse.go
package commands

import (
	"fmt"
	"os"
	"path/filepath"

	"arkhe/parser/frontends/twitch"
    "arkhe/parser/lfir"
	"github.com/spf13/cobra"
)

var twitchParseCmd = &cobra.Command{
	Use:   "parse --file <data> [--channel <name>] [--realtime]",
	Short: "Parse Twitch streaming data into LFIR graphs with coherence metrics",
	Long: `Analyze Twitch channels, streams, chat, and community for coherence metrics.

Supported inputs:
  • Channel export JSON from Twitch API
  • Chat logs in IRC format (.txt, .log, .irc)
  • Stream metrics JSON
  • Live stream monitoring via API (requires credentials)

Key analyses:
  • Content consistency: category/branding alignment
  • Schedule adherence: stream timing predictability
  • Community health: sentiment, retention, growth
  • Monetization balance: revenue source diversification
  • Moderation effectiveness: toxicity management
  • Real-time coherence: live stream engagement quality

Examples:
  arkhe twitch parse --file channel_export.json
  arkhe twitch parse --file chat_log.txt --channel xqc
  arkhe twitch parse --channel "pokimane" --client-id xxx --realtime
  arkhe twitch parse --file stream_metrics.json --output lfir.json`,
	RunE: runTwitchParse,
}

var (
	twitchFile        string
	twitchChannel     string
	twitchClientID    string
	twitchClientSecret string
	twitchAccessToken  string
	twitchOutput      string
	twitchVerbose     bool
	twitchRealtime    bool
)

func init() {
	twitchParseCmd.Flags().StringVarP(&twitchFile, "file", "f", "", "Path to Twitch data file")
	twitchParseCmd.Flags().StringVarP(&twitchChannel, "channel", "c", "", "Twitch channel name (for API fetch)")
	twitchParseCmd.Flags().StringVar(&twitchClientID, "client-id", "", "Twitch API Client ID")
	twitchParseCmd.Flags().StringVar(&twitchClientSecret, "client-secret", "", "Twitch API Client Secret")
	twitchParseCmd.Flags().StringVar(&twitchAccessToken, "access-token", "", "Twitch OAuth access token")
	twitchParseCmd.Flags().StringVarP(&twitchOutput, "output", "o", "", "Output path for LFIR JSON")
	twitchParseCmd.Flags().BoolVarP(&twitchVerbose, "verbose", "v", false, "Verbose output with detailed metrics")
	twitchParseCmd.Flags().BoolVar(&twitchRealtime, "realtime", false, "Enable real-time coherence monitoring")
	twitchParseCmd.MarkFlagsOneRequired("file", "channel")
}

func runTwitchParse(cmd *cobra.Command, args []string) error {
	// Configure parser
	parser := twitch.NewTwitchParser()
	parser.ClientID = twitchClientID
	parser.ClientSecret = twitchClientSecret
	parser.AccessToken = twitchAccessToken
	parser.RealtimeMode = twitchRealtime

	// Parse from file or API
	var graph *lfir.LFIRGraph
	var err error

	if twitchFile != "" {
		source, err := os.ReadFile(twitchFile)
		if err != nil {
			return fmt.Errorf("failed to read file: %w", err)
		}
		graph, err = parser.Parse(source, filepath.Base(twitchFile), map[string]interface{}{
			"channel_name": twitchChannel,
		})
	} else if twitchChannel != "" {
		graph, err = parser.Parse(nil, "api_fetch", map[string]interface{}{
			"channel_name": twitchChannel,
		})
	}

	if err != nil {
		return fmt.Errorf("parse failed: %w", err)
	}

	// Verbose output
	if twitchVerbose {
		fmt.Printf("📺 ARKHE Twitch Analysis — %s\n", twitchChannel)
		fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
		printTwitchStats(graph)
	}

	// Save output
	if twitchOutput != "" {
		if err := graph.ToJSONFile(twitchOutput); err != nil {
			return fmt.Errorf("failed to write output: %w", err)
		}
		fmt.Printf("✅ LFIR graph saved to %s\n", twitchOutput)
	}

	// Coherence summary
	coherence := graph.Metrics.CoherenceScore
	status := "✅"
	if coherence < 0.7 {
		status = "⚠️"
	}
	if coherence < 0.5 {
		status = "❌"
	}
	fmt.Printf("• Φ_C (Channel Coherence) = %.2f %s\n", coherence, status)

	// Component breakdown
	root := graph.Nodes[graph.RootNodes[0]]
	fmt.Printf("\nComponent Scores:\n")
	fmt.Printf("  • Content Consistency: %.2f\n", root.Attributes["coherence_content_consistency"])
	fmt.Printf("  • Schedule Adherence: %.2f\n", root.Attributes["coherence_schedule_adherence"])
	fmt.Printf("  • Community Health: %.2f\n", root.Attributes["coherence_community_health"])
	fmt.Printf("  • Monetization Balance: %.2f\n", root.Attributes["coherence_monetization_balance"])

	if toxicity := root.Attributes["coherence_toxicity_penalty"]; toxicity != nil {
		fmt.Printf("  • Toxicity Penalty: %.2f\n", toxicity)
	}

	// Alerts
	if root.Attributes["is_live"] == true && twitchRealtime {
		if realtimeCoherence, ok := root.Attributes["realtime_coherence"].(float64); ok {
			if realtimeCoherence < 0.6 {
				fmt.Printf("\n⚠️  Real-time coherence low: %.2f — consider engagement interventions\n", realtimeCoherence)
			}
		}
	}

	return nil
}

func printTwitchStats(graph *lfir.LFIRGraph) {
	root := graph.Nodes[graph.RootNodes[0]]

	fmt.Printf("• Canal: %s (%s)\n", root.Attributes["channel_name"], root.Attributes["channel_id"])
	fmt.Printf("• Ao vivo: %v\n", root.Attributes["is_live"])
	fmt.Printf("• Seguidores: %d\n", root.Attributes["follower_count"])
	fmt.Printf("• Visualizações totais: %d\n", root.Attributes["total_views"])

	if root.Attributes["is_live"] == true {
		fmt.Printf("\n🔴 Stream Atual:\n")
		fmt.Printf("  • Título: %s\n", root.Attributes["live_title"])
		fmt.Printf("  • Categoria: %s\n", root.Attributes["category"])
		fmt.Printf("  • Viewers: %d\n", root.Attributes["live_viewers"])
	}

	if chatMsgs, ok := root.Attributes["chat_message_count"].(int); ok && chatMsgs > 0 {
		fmt.Printf("\n💬 Chat:\n")
		fmt.Printf("  • Mensagens: %d\n", chatMsgs)
	}
}
