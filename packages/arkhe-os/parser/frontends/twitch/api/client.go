// parser/frontends/twitch/api/client.go
package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"time"
)

// Client representa cliente para Twitch API
type Client struct {
	httpClient  *http.Client
	clientID    string
	clientSecret string
	accessToken string
	baseURL     string
	rateLimiter *RateLimiter
}

// NewClient cria novo cliente Twitch API
func NewClient(clientID, clientSecret, accessToken string) *Client {
	return &Client{
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		clientID:    clientID,
		clientSecret: clientSecret,
		accessToken: accessToken,
		baseURL:     "https://api.twitch.tv/helix",
		rateLimiter: NewRateLimiter(800, time.Minute), // Twitch limit: 800 req/min
	}
}

// ChannelData representa dados de canal da Twitch API
type ChannelData struct {
	ID            string     `json:"broadcaster_id"`
	Name          string     `json:"broadcaster_login"`
	DisplayName   string     `json:"broadcaster_name"`
	Description   string     `json:"description"`
	CreatedAt     time.Time  `json:"created_at"`
	FollowerCount int        `json:"follower_count"`
	ViewCount     int        `json:"view_count"`
	Category      string     `json:"game_name"`
	Tags          []string   `json:"tags"`
	Language      string     `json:"broadcaster_language"`
	Mature        bool       `json:"is_mature"`
	LiveStream    *StreamData `json:"stream,omitempty"`
}

// StreamData representa dados de stream ao vivo
type StreamData struct {
	ID           string    `json:"id"`
	UserID       string    `json:"user_id"`
	UserName     string    `json:"user_name"`
	GameID       string    `json:"game_id"`
	GameName     string    `json:"game_name"`
	Type         string    `json:"type"` // "live" or ""
	Title        string    `json:"title"`
	ViewerCount  int       `json:"viewer_count"`
	StartedAt    time.Time `json:"started_at"`
	Language     string    `json:"language"`
	ThumbnailURL string    `json:"thumbnail_url"`
	TagIDs       []string  `json:"tag_ids"`
	IsMature     bool      `json:"is_mature"`
}

// GetChannel busca dados de um canal por nome
func (c *Client) GetChannel(ctx context.Context, channelName string) (*ChannelData, error) {
	// Primeiro buscar user ID pelo login
	users, err := c.GetUsersByLogin(ctx, []string{channelName})
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	if len(users) == 0 {
		return nil, fmt.Errorf("channel not found: %s", channelName)
	}
	user := users[0]

	// Buscar dados do canal
	params := url.Values{}
	params.Add("broadcaster_id", user.ID)

	var response struct {
		Data []ChannelData `json:"data"`
	}

	if err := c.doRequest(ctx, "GET", "/channels", params, &response); err != nil {
		return nil, err
	}

	if len(response.Data) == 0 {
		return nil, fmt.Errorf("no channel data found for %s", channelName)
	}

	channel := &response.Data[0]

	// Verificar se está ao vivo
	streams, err := c.GetStreamsByUserID(ctx, user.ID)
	if err == nil && len(streams) > 0 {
		channel.LiveStream = &streams[0]
	}

	return channel, nil
}

// GetUsersByLogin busca usuários por login name
func (c *Client) GetUsersByLogin(ctx context.Context, logins []string) ([]UserData, error) {
	params := url.Values{}
	for _, login := range logins {
		params.Add("login", login)
	}

	var response struct {
		Data []UserData `json:"data"`
	}

	if err := c.doRequest(ctx, "GET", "/users", params, &response); err != nil {
		return nil, err
	}

	return response.Data, nil
}

// UserData representa dados básicos de usuário
type UserData struct {
	ID              string    `json:"id"`
	Login           string    `json:"login"`
	DisplayName     string    `json:"display_name"`
	Type            string    `json:"type"` // "admin", "global_mod", "staff", ""
	BroadcasterType string    `json:"broadcaster_type"` // "partner", "affiliate", ""
	Description     string    `json:"description"`
	CreatedAt       time.Time `json:"created_at"`
}

// GetStreamsByUserID busca streams por user ID
func (c *Client) GetStreamsByUserID(ctx context.Context, userID string) ([]StreamData, error) {
	params := url.Values{}
	params.Add("user_id", userID)

	var response struct {
		Data []StreamData `json:"data"`
	}

	if err := c.doRequest(ctx, "GET", "/streams", params, &response); err != nil {
		return nil, err
	}

	return response.Data, nil
}

// GetChannelStreams busca histórico de streams de um canal
func (c *Client) GetChannelStreams(ctx context.Context, userID string, limit int) ([]StreamData, error) {
	params := url.Values{}
	params.Add("user_id", userID)
	params.Add("first", fmt.Sprintf("%d", min(limit, 100)))

	var streams []StreamData
	var cursor string

	for {
		if cursor != "" {
			params.Set("after", cursor)
		}

		var response struct {
			Data       []StreamData `json:"data"`
			Pagination struct {
				Cursor string `json:"cursor"`
			} `json:"pagination"`
		}

		if err := c.doRequest(ctx, "GET", "/streams", params, &response); err != nil {
			return nil, err
		}

		streams = append(streams, response.Data...)

		cursor = response.Pagination.Cursor
		if cursor == "" || len(streams) >= limit {
			break
		}
	}

	return streams, nil
}

// doRequest executa request HTTP com autenticação e rate limiting
func (c *Client) doRequest(ctx context.Context, method, endpoint string, params url.Values, result interface{}) error {
	// Rate limiting
	if err := c.rateLimiter.Wait(ctx); err != nil {
		return fmt.Errorf("rate limit exceeded: %w", err)
	}

	// Construir URL
	u, err := url.Parse(c.baseURL + endpoint)
	if err != nil {
		return err
	}
	u.RawQuery = params.Encode()

	// Criar request
	req, err := http.NewRequestWithContext(ctx, method, u.String(), nil)
	if err != nil {
		return err
	}

	// Headers obrigatórios da Twitch API
	req.Header.Set("Client-ID", c.clientID)
	if c.accessToken != "" {
		req.Header.Set("Authorization", "Bearer "+c.accessToken)
	}
	req.Header.Set("Content-Type", "application/json")

	// Executar request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	// Verificar status
	if resp.StatusCode >= 400 {
		var errorResp struct {
			Error   string `json:"error"`
			Status  int    `json:"status"`
			Message string `json:"message"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&errorResp); err == nil {
			return fmt.Errorf("API error %d: %s - %s", resp.StatusCode, errorResp.Error, errorResp.Message)
		}
		return fmt.Errorf("API error %d", resp.StatusCode)
	}

	// Parse response
	return json.NewDecoder(resp.Body).Decode(result)
}

// GetFollowers mock
func (c *Client) GetFollowers(ctx context.Context, channelID string, limit int) ([]interface{}, error) {
    return nil, nil
}

// GetSubscribers mock
func (c *Client) GetSubscribers(ctx context.Context, channelID string, limit int) ([]interface{}, error) {
    return nil, nil
}

// GetRevenueSummary mock
func (c *Client) GetRevenueSummary(ctx context.Context, channelID string, period string) ([]interface{}, error) {
    return nil, nil
}

// RateLimiter implementa rate limiting simples
type RateLimiter struct {
	tokens     chan struct{}
	refillRate time.Duration
}

func NewRateLimiter(maxTokens int, refillRate time.Duration) *RateLimiter {
	rl := &RateLimiter{
		tokens:     make(chan struct{}, maxTokens),
		refillRate: refillRate,
	}

	// Preencher tokens iniciais
	for i := 0; i < maxTokens; i++ {
		rl.tokens <- struct{}{}
	}

	// Goroutine para refill
	go func() {
		ticker := time.NewTicker(refillRate)
		for range ticker.C {
			select {
			case rl.tokens <- struct{}{}:
			default:
				// Canal cheio, ignorar
			}
		}
	}()

	return rl
}

func (rl *RateLimiter) Wait(ctx context.Context) error {
	select {
	case <-rl.tokens:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// Helpers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
