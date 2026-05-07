// parser/frontends/twitch/models/lfir_mapping.go
package models

import (
	"fmt"

	"arkhe/parser/lfir"
)

// Tipos de nós LFIR específicos para Twitch
const (
	// Entidades principais
	LFIRNodeTypeChannel      lfir.LFIRNodeType = "twitch_channel"
	LFIRNodeTypeStream       lfir.LFIRNodeType = "twitch_stream"
	LFIRNodeTypeVOD          lfir.LFIRNodeType = "twitch_vod"
	LFIRNodeTypeClip         lfir.LFIRNodeType = "twitch_clip"

	// Comunidade
	LFIRNodeTypeUser         lfir.LFIRNodeType = "twitch_user"
	LFIRNodeTypeFollower     lfir.LFIRNodeType = "twitch_follower"
	LFIRNodeTypeSubscriber   lfir.LFIRNodeType = "twitch_subscriber"
	LFIRNodeTypeModerator    lfir.LFIRNodeType = "twitch_moderator"

	// Chat
	LFIRNodeTypeChatMessage  lfir.LFIRNodeType = "twitch_chat_message"
	LFIRNodeTypeEmote        lfir.LFIRNodeType = "twitch_emote"
	LFIRNodeTypeBadge        lfir.LFIRNodeType = "twitch_badge"

	// Eventos
	LFIRNodeTypeRaid         lfir.LFIRNodeType = "twitch_raid"
	LFIRNodeTypeHost         lfir.LFIRNodeType = "twitch_host"
	LFIRNodeTypeSubscription lfir.LFIRNodeType = "twitch_subscription"
	LFIRNodeTypeCheer        lfir.LFIRNodeType = "twitch_cheer"

	// Monetização
	LFIRNodeTypeRevenue      lfir.LFIRNodeType = "twitch_revenue"
	LFIRNodeTypeSponsorship  lfir.LFIRNodeType = "twitch_sponsorship"

	// Moderação
	LFIRNodeTypeModeration   lfir.LFIRNodeType = "twitch_moderation"
	LFIRNodeTypeBan          lfir.LFIRNodeType = "twitch_ban"
	LFIRNodeTypeTimeout      lfir.LFIRNodeType = "twitch_timeout"

	// Alertas
	LFIRNodeTypeAlert        lfir.LFIRNodeType = "twitch_alert"
)

// TwitchLFIRBuilder converte modelo Twitch → grafo LFIR
type TwitchLFIRBuilder struct {
	graph         *lfir.LFIRGraph
	rootID        string
	userNodeMap   map[string]string // UserID → LFIR node ID
	streamNodeMap map[string]string // StreamID → LFIR node ID
}

func NewTwitchLFIRBuilder(graph *lfir.LFIRGraph, rootID string) *TwitchLFIRBuilder {
	return &TwitchLFIRBuilder{
		graph:         graph,
		rootID:        rootID,
		userNodeMap:   make(map[string]string),
		streamNodeMap: make(map[string]string),
	}
}

// Build converte canal Twitch para LFIR
func (b *TwitchLFIRBuilder) Build(channel *Channel) error {
	// Criar nó do canal
	channelNode := b.createChannelNode(channel)
	b.graph.AddNode(channelNode)
	b.graph.Link(b.rootID, channelNode.ID)

	// Criar nó da stream atual se ao vivo
	if channel.LiveStream != nil {
		streamNode := b.createStreamNode(channel.LiveStream, true)
		b.graph.AddNode(streamNode)
		b.graph.Link(channelNode.ID, streamNode.ID)
		b.streamNodeMap[channel.LiveStream.ID] = streamNode.ID
	}

	// Criar nós de streams históricas
	for _, stream := range channel.Streams {
        s := stream
		streamNode := b.createStreamNode(&s, false)
		b.graph.AddNode(streamNode)
		b.graph.Link(channelNode.ID, streamNode.ID)
		b.streamNodeMap[stream.ID] = streamNode.ID
	}

	// Criar nós de chat messages (amostragem para performance)
	if channel.Chat != nil && len(channel.Chat.Messages) > 0 {
		sampleSize := min(len(channel.Chat.Messages), 1000)
		for i := 0; i < sampleSize; i++ {
			msg := channel.Chat.Messages[i]
			msgNode := b.createChatMessageNode(&msg)
			b.graph.AddNode(msgNode)
			b.graph.Link(channelNode.ID, msgNode.ID)

			// Link para usuário
			if msg.Username != "" {
				userNode := b.getOrCreateUserNode(msg.Username)
				b.graph.Link(userNode.ID, msgNode.ID)
			}

			// Link para emotes
			for _, emote := range msg.Emotes {
				emoteNode := b.createEmoteNode(emote)
				b.graph.AddNode(emoteNode)
				b.graph.Link(msgNode.ID, emoteNode.ID)
			}
		}
	}

	// Criar nós de seguidores/subscribers (amostragem)
	for i, follower := range channel.Followers {
		if i >= 100 { // Limitar amostra
			break
		}
		followerNode := b.createFollowerNode(follower)
		b.graph.AddNode(followerNode)
		b.graph.Link(channelNode.ID, followerNode.ID)
	}

	for i, sub := range channel.Subscribers {
		if i >= 100 {
			break
		}
		subNode := b.createSubscriberNode(sub)
		b.graph.AddNode(subNode)
		b.graph.Link(channelNode.ID, subNode.ID)
	}

	// Criar nós de receita
	for _, rev := range channel.Revenue {
		revNode := b.createRevenueNode(rev)
		b.graph.AddNode(revNode)
		b.graph.Link(channelNode.ID, revNode.ID)
	}

	// Criar nós de ações de moderação
	for _, action := range channel.ModerationActions {
		modNode := b.createModerationNode(action)
		b.graph.AddNode(modNode)
		b.graph.Link(channelNode.ID, modNode.ID)

		// Link para usuário afetado
		if action.Target != "" {
			userNode := b.getOrCreateUserNode(action.Target)
			b.graph.Link(modNode.ID, userNode.ID)
		}
	}

	// Criar arestas de eventos (raids, hosts)
	b.addEventEdges(channel)

	return nil
}

func (b *TwitchLFIRBuilder) createChannelNode(channel *Channel) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeChannel,
		fmt.Sprintf("channel_%s", channel.ID), "twitch")

	node.Attributes["id"] = channel.ID
	node.Attributes["name"] = channel.Name
	node.Attributes["display_name"] = channel.DisplayName
	node.Attributes["description"] = channel.Description
	node.Attributes["created_at"] = channel.CreatedAt.Unix()
	node.Attributes["follower_count"] = channel.FollowerCount
	node.Attributes["total_views"] = channel.TotalViews
	node.Attributes["category"] = channel.Category
	node.Attributes["language"] = channel.Language
	node.Attributes["mature"] = channel.Mature
	node.Attributes["partner"] = channel.Partner
	node.Attributes["affiliate"] = channel.Affiliate
	node.Attributes["is_live"] = channel.LiveStream != nil

	if channel.LiveStream != nil {
		node.Attributes["live_title"] = channel.LiveStream.Title
		node.Attributes["live_viewers"] = channel.LiveStream.ViewerCount
		node.Attributes["live_started_at"] = channel.LiveStream.StartedAt.Unix()
	}

	if len(channel.Tags) > 0 {
		node.Attributes["tags"] = channel.Tags
	}

	return node
}

func (b *TwitchLFIRBuilder) createStreamNode(stream *Stream, isLive bool) *lfir.LFIRNode {
	nodeType := LFIRNodeTypeStream
	if !isLive {
		nodeType = LFIRNodeTypeVOD
	}

	node := lfir.NewLFIRNode(nodeType,
		fmt.Sprintf("stream_%s", stream.ID), "twitch")

	node.Attributes["id"] = stream.ID
	node.Attributes["title"] = stream.Title
	node.Attributes["category"] = stream.Category
	node.Attributes["started_at"] = stream.StartedAt.Unix()
	if !stream.EndedAt.IsZero() {
		node.Attributes["ended_at"] = stream.EndedAt.Unix()
		node.Attributes["duration_minutes"] = stream.Duration.Minutes()
	}
	node.Attributes["peak_viewers"] = stream.PeakViewers
	node.Attributes["avg_viewers"] = stream.AvgViewers
	node.Attributes["language"] = stream.Language
	node.Attributes["is_mature"] = stream.IsMature

	// Engajamento
	if stream.ChatMessages > 0 {
		node.Attributes["chat_messages"] = stream.ChatMessages
		node.Attributes["unique_chatters"] = stream.UniqueChatters
	}

	// Eventos
	if stream.RaidsReceived > 0 {
		node.Attributes["raids_received"] = stream.RaidsReceived
	}
	if stream.RaidsSent > 0 {
		node.Attributes["raids_sent"] = stream.RaidsSent
	}

	if len(stream.Tags) > 0 {
		node.Attributes["tags"] = stream.Tags
	}

	return node
}

func (b *TwitchLFIRBuilder) createChatMessageNode(msg *ChatMessage) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeChatMessage,
		fmt.Sprintf("msg_%s", msg.ID), "twitch")

	node.Attributes["username"] = msg.Username
	node.Attributes["display_name"] = msg.DisplayName
	node.Attributes["content"] = truncateString(msg.Content, 200)
	node.Attributes["timestamp"] = msg.Timestamp.Unix()
	node.Attributes["message_type"] = string(msg.MessageType)

	if msg.Color != "" {
		node.Attributes["color"] = msg.Color
	}
	if len(msg.Badges) > 0 {
		node.Attributes["badges"] = msg.Badges
	}
	if msg.Sentiment != 0 {
		node.Attributes["sentiment"] = msg.Sentiment
	}
	if msg.IsToxic {
		node.Attributes["is_toxic"] = true
	}
	if msg.IsSpam {
		node.Attributes["is_spam"] = true
	}
	if msg.IsCommand {
		node.Attributes["is_command"] = true
	}
	if len(msg.Emotes) > 0 {
		emoteIDs := make([]string, len(msg.Emotes))
		for i, e := range msg.Emotes {
			emoteIDs[i] = e.ID
		}
		node.Attributes["emote_ids"] = emoteIDs
	}

	return node
}

func (b *TwitchLFIRBuilder) getOrCreateUserNode(username string) *lfir.LFIRNode {
	// Verificar se já existe
	if nodeID, exists := b.userNodeMap[username]; exists {
		return b.graph.Nodes[nodeID]
	}

	// Criar novo nó
	node := lfir.NewLFIRNode(LFIRNodeTypeUser,
		fmt.Sprintf("user_%s", username), "twitch")
	node.Attributes["username"] = username
	node.Attributes["display_name"] = username // Pode ser atualizado depois

	b.graph.AddNode(node)
	b.userNodeMap[username] = node.ID

	return node
}

func (b *TwitchLFIRBuilder) createEmoteNode(emote EmoteRef) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeEmote,
		fmt.Sprintf("emote_%s", emote.ID), "twitch")
	node.Attributes["id"] = emote.ID
	node.Attributes["text"] = emote.Text
	return node
}

func (b *TwitchLFIRBuilder) createFollowerNode(follower Follower) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeFollower,
		fmt.Sprintf("follower_%s", follower.UserID), "twitch")
	node.Attributes["user_id"] = follower.UserID
	node.Attributes["user_name"] = follower.UserName
	node.Attributes["followed_at"] = follower.FollowedAt.Unix()
	return node
}

func (b *TwitchLFIRBuilder) createSubscriberNode(sub Subscriber) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeSubscriber,
		fmt.Sprintf("sub_%s", sub.UserID), "twitch")
	node.Attributes["user_id"] = sub.UserID
	node.Attributes["user_name"] = sub.UserName
	node.Attributes["tier"] = sub.Tier
	node.Attributes["subscribed_at"] = sub.SubscribedAt.Unix()
	if sub.StreakMonths > 0 {
		node.Attributes["streak_months"] = sub.StreakMonths
	}
	return node
}

func (b *TwitchLFIRBuilder) createRevenueNode(rev RevenueEntry) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeRevenue,
		fmt.Sprintf("rev_%s_%d", rev.Type, rev.Timestamp.Unix()), "twitch")
	node.Attributes["type"] = rev.Type
	node.Attributes["amount"] = rev.Amount
	node.Attributes["currency"] = rev.Currency
	node.Attributes["timestamp"] = rev.Timestamp.Unix()
	if rev.UserID != "" {
		node.Attributes["user_id"] = rev.UserID
	}
	if rev.Tier != "" {
		node.Attributes["tier"] = rev.Tier
	}
	if rev.Bits > 0 {
		node.Attributes["bits"] = rev.Bits
	}
	return node
}

func (b *TwitchLFIRBuilder) createModerationNode(action ModerationAction) *lfir.LFIRNode {
	nodeType := LFIRNodeTypeModeration
	if action.Type == MsgTypeBan {
		nodeType = LFIRNodeTypeBan
	} else if action.Type == MsgTypeTimeout {
		nodeType = LFIRNodeTypeTimeout
	}

	node := lfir.NewLFIRNode(nodeType,
		fmt.Sprintf("mod_%s_%d", action.Target, action.Timestamp.Unix()), "twitch")
	node.Attributes["type"] = string(action.Type)
	node.Attributes["target"] = action.Target
	node.Attributes["timestamp"] = action.Timestamp.Unix()
	if action.Moderator != "" {
		node.Attributes["moderator"] = action.Moderator
	}
	if action.Duration > 0 {
		node.Attributes["duration_seconds"] = action.Duration.Seconds()
	}
	if action.Reason != "" {
		node.Attributes["reason"] = action.Reason
	}
	return node
}

func (b *TwitchLFIRBuilder) addEventEdges(channel *Channel) {
	// Adicionar arestas para raids/hosts entre streams
	// (implementação futura: parsear eventos de raid/host do chat)
}

// Helpers
func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
