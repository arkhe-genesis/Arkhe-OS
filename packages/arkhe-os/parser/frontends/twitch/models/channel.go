// parser/frontends/twitch/models/channel.go
package models

import (
	"time"
)

// Channel representa um canal da Twitch
type Channel struct {
	ID              string         `json:"id"`
	Name            string         `json:"name"`
	DisplayName     string         `json:"display_name"`
	Description     string         `json:"description,omitempty"`
	CreatedAt       time.Time      `json:"created_at"`
	FollowerCount   int            `json:"follower_count"`
	TotalViews      int            `json:"total_views"`
	Category        string         `json:"category,omitempty"`
	Tags            []string       `json:"tags,omitempty"`
	Language        string         `json:"language"`
	Mature          bool           `json:"mature"`
	Partner         bool           `json:"partner"`
	Affiliate       bool           `json:"affiliate"`

	// Stream atual (se ao vivo)
	LiveStream      *Stream        `json:"live_stream,omitempty"`

	// Histórico de streams
	Streams         []Stream       `json:"streams,omitempty"`

	// Chat
	Chat            *ChatLog       `json:"chat,omitempty"`

	// Comunidade
	Followers       []Follower     `json:"followers,omitempty"`
	Subscribers     []Subscriber   `json:"subscribers,omitempty"`
	VIPs            []string       `json:"vips,omitempty"`
	Moderators      []string       `json:"moderators,omitempty"`

	// Monetização
	Revenue         []RevenueEntry `json:"revenue,omitempty"`
	Sponsorships    []Sponsorship  `json:"sponsorships,omitempty"`

	// Moderação
	ModerationActions []ModerationAction `json:"moderation_actions,omitempty"`

	// Metadados
	LastUpdated   time.Time      `json:"last_updated"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// Stream representa uma transmissão (ao vivo ou VOD)
type Stream struct {
	ID            string    `json:"id"`
	Type          string    `json:"type"` // "live", "vod", "clip"
	Title         string    `json:"title"`
	Category      string    `json:"category"`
	StartedAt     time.Time `json:"started_at"`
	EndedAt       time.Time `json:"ended_at,omitempty"`
	Duration      time.Duration `json:"duration,omitempty"`
	ViewerCount   int       `json:"viewer_count"`
	PeakViewers   int       `json:"peak_viewers,omitempty"`
	AvgViewers    int       `json:"avg_viewers,omitempty"`
	Language      string    `json:"language"`
	ThumbnailURL  string    `json:"thumbnail_url,omitempty"`
	VideoURL      string    `json:"video_url,omitempty"`
	Tags          []string  `json:"tags,omitempty"`
	IsMature      bool      `json:"is_mature"`

	// Métricas de engajamento
	ChatMessages  int       `json:"chat_messages,omitempty"`
	UniqueChatters int      `json:"unique_chatters,omitempty"`
	RaidsReceived int       `json:"raids_received,omitempty"`
	RaidsSent     int       `json:"raids_sent,omitempty"`
	HostsReceived int       `json:"hosts_received,omitempty"`
}

// ChatLog representa log de chat de uma stream
type ChatLog struct {
	StreamID      string         `json:"stream_id"`
	StartTime     time.Time      `json:"start_time"`
	EndTime       time.Time      `json:"end_time"`
	Messages      []ChatMessage  `json:"messages"`
	TotalMessages int            `json:"total_messages"`
	UniqueUsers   int            `json:"unique_users"`
	MsgsPerMinute float64        `json:"msgs_per_minute"`

	// Métricas derivadas
	AvgSentiment  float64        `json:"avg_sentiment,omitempty"`
	ToxicityRate  float64        `json:"toxicity_rate,omitempty"`
	SpamRate      float64        `json:"spam_rate,omitempty"`
	CommandRate   float64        `json:"command_rate,omitempty"`
}

// ChatMessage representa uma mensagem de chat
type ChatMessage struct {
	ID            string         `json:"id"`
	Username      string         `json:"username"`
	DisplayName   string         `json:"display_name"`
	Content       string         `json:"content"`
	Timestamp     time.Time      `json:"timestamp"`
	Color         string         `json:"color,omitempty"`
	Badges        []string       `json:"badges,omitempty"`
	Emotes        []EmoteRef     `json:"emotes,omitempty"`
	MessageType   MessageType    `json:"message_type"`
	Sentiment     float64        `json:"sentiment,omitempty"` // -1 a +1
	IsToxic       bool           `json:"is_toxic,omitempty"`
	IsSpam        bool           `json:"is_spam,omitempty"`
	IsCommand     bool           `json:"is_command,omitempty"`
	RawTags       map[string]string `json:"raw_tags,omitempty"`
	RawLine       string         `json:"raw_line,omitempty"`
	Valid         bool           `json:"valid"`
}

// MessageType define tipos de mensagem de chat
type MessageType string

const (
	MsgTypeChat        MessageType = "chat"
	MsgTypeSubscription MessageType = "subscription"
	MsgTypeCheer       MessageType = "cheer"
	MsgTypeRaid        MessageType = "raid"
	MsgTypeRitual      MessageType = "ritual"
	MsgTypeTimeout     MessageType = "timeout"
	MsgTypeBan         MessageType = "ban"
	MsgTypeModeration  MessageType = "moderation"
	MsgTypeCommand     MessageType = "command"
	MsgTypeMention     MessageType = "mention"
	MsgTypeSystem      MessageType = "system"
)

// EmoteRef representa referência a um emote na mensagem
type EmoteRef struct {
	ID    string `json:"id"`
	Text  string `json:"text"`
	Start int    `json:"start"`
	End   int    `json:"end"`
}

// Follower representa um seguidor do canal
type Follower struct {
	UserID    string    `json:"user_id"`
	UserName  string    `json:"user_name"`
	FollowedAt time.Time `json:"followed_at"`
}

// Subscriber representa um subscriber do canal
type Subscriber struct {
	UserID       string    `json:"user_id"`
	UserName     string    `json:"user_name"`
	Tier         string    `json:"tier"` // "1000", "2000", "3000"
	SubscribedAt time.Time `json:"subscribed_at"`
	StreakMonths int       `json:"streak_months,omitempty"`
}

// RevenueEntry representa uma entrada de receita
type RevenueEntry struct {
	Type        string    `json:"type"` // "subscription", "bit", "donation", "ad", "sponsorship"
	Amount      float64   `json:"amount"`
	Currency    string    `json:"currency"`
	Timestamp   time.Time `json:"timestamp"`
	UserID      string    `json:"user_id,omitempty"`
	Tier        string    `json:"tier,omitempty"` // Para subs
	Bits        int       `json:"bits,omitempty"`  // Para cheers
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Sponsorship representa um patrocínio
type Sponsorship struct {
	ID          string    `json:"id"`
	SponsorName string    `json:"sponsor_name"`
	StartDate   time.Time `json:"start_date"`
	EndDate     time.Time `json:"end_date,omitempty"`
	Value       float64   `json:"value,omitempty"`
	Currency    string    `json:"currency,omitempty"`
	Requirements []string `json:"requirements,omitempty"`
	Controversial bool    `json:"controversial,omitempty"`
}

// ModerationAction representa uma ação de moderação
type ModerationAction struct {
	Type      MessageType `json:"type"` // timeout, ban, etc.
	Target    string      `json:"target"`
	Moderator string      `json:"moderator,omitempty"`
	Timestamp time.Time   `json:"timestamp"`
	Duration  time.Duration `json:"duration,omitempty"` // Para timeouts
	Reason    string      `json:"reason,omitempty"`
}
