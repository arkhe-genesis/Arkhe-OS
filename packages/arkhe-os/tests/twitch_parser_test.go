// tests/twitch_parser_test.go
package tests

import (
	"os"
	"testing"
    "time"

	"arkhe/parser/frontends/twitch"
	"github.com/stretchr/testify/assert"
)

func TestTwitchParser_ChannelExport(t *testing.T) {
	parser := twitch.NewTwitchParser()

	// Load sample channel export
	source, err := os.ReadFile("examples/twitch/channel_export.json")
	assert.NoError(t, err)

	graph, err := parser.Parse(source, "channel_export.json", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)

	// Verify coherence is in valid range
	assert.GreaterOrEqual(t, graph.Metrics.CoherenceScore, 0.0)
	assert.LessOrEqual(t, graph.Metrics.CoherenceScore, 1.0)

	// Verify expected attributes
	root := graph.Nodes[graph.RootNodes[0]]
	assert.NotEmpty(t, root.Attributes["channel_id"])
	assert.NotEmpty(t, root.Attributes["channel_name"])
	assert.GreaterOrEqual(t, root.Attributes["follower_count"], 0)
    _ = root
}

func TestTwitchParser_ChatLog(t *testing.T) {
	parser := twitch.NewTwitchParser()
	parser.AnalyzeChat = true

	// Sample Twitch IRC chat log
	source := []byte(`@badge-info=;badges=staff/1,admin/1;color=#0000FF;display-name=Twitch;emotes=;flags=;id=abc123;mod=1;room-id=12345;subscriber=0;tmi-sent-ts=1234567890000;turbo=0;user-id=12345;user-type=staff :twitch!twitch@twitch.tmi.twitch.tv PRIVMSG #xqc :Welcome to the stream!
@badge-info=subscriber/12;badges=subscriber/12;color=#FF69B4;display-name=FAN123;emotes=;flags=;id=def456;mod=0;room-id=12345;subscriber=1;tmi-sent-ts=1234567891000;turbo=0;user-id=67890;user-type= :fan123!fan123@fan123.tmi.twitch.tv PRIVMSG #xqc :Love this content! <3
@msg-id=timeout :tmi.twitch.tv NOTICE #xqc :User123 has been timed out for 600 seconds. Reason: spam
`)

	graph, err := parser.Parse(source, "chat_log.txt", map[string]interface{}{
		"channel_name": "xqc",
	})
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	// Should parse chat messages
	assert.Greater(t, root.Attributes["chat_message_count"].(int), 0)

	// Community health should reflect positive sentiment
	communityHealth := root.Attributes["coherence_community_health"].(float64)
	assert.Greater(t, communityHealth, 0.5)
}

func TestTwitchParser_RealtimeCoherence(t *testing.T) {
	parser := twitch.NewTwitchParser()
	parser.RealtimeMode = true
	parser.CoherenceWindow = 1 * time.Minute

	// Sample live stream data
	source := []byte(`{
		"stream": {
			"id": "live_123",
			"title": "Speedrunning Celeste any%",
			"category": "Celeste",
			"viewer_count": 1500,
			"started_at": "2024-05-07T18:00:00Z",
			"chat_messages": 450,
			"unique_chatters": 280
		},
		"chat_window": {
			"messages_per_minute": 75,
			"avg_sentiment": 0.65,
			"toxicity_rate": 0.02
		}
	}`)

	graph, err := parser.Parse(source, "live_stream.json", map[string]interface{}{
		"channel_name": "speedrunner_pro",
	})
	assert.NoError(t, err)

	// High engagement + low toxicity should yield good coherence
	coherence := graph.Metrics.CoherenceScore
	assert.Greater(t, coherence, 0.5)
}

func TestTwitchParser_MonetizationBalance(t *testing.T) {
	parser := twitch.NewTwitchParser()
	parser.AnalyzeMonetization = true

	// Channel with diverse revenue sources
	source := []byte(`{
		"channel": {
			"name": "balanced_creator",
			"revenue": [
				{"type": "subscription", "amount": 5000, "currency": "USD"},
				{"type": "bits", "amount": 1200, "currency": "USD"},
				{"type": "donation", "amount": 800, "currency": "USD"},
				{"type": "sponsorship", "amount": 3000, "currency": "USD"}
			]
		}
	}`)

	graph, err := parser.Parse(source, "revenue.json", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	// Diverse revenue should yield high monetization balance
	monetizationBalance := root.Attributes["coherence_monetization_balance"].(float64)
	assert.Greater(t, monetizationBalance, 0.5)
}
