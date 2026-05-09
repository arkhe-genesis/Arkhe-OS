// parser/frontends/twitch/parsers/chat_parser.go
package parsers

import (
	"bufio"
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"time"

	"arkhe/parser/frontends/twitch/models"
)

// ParseChatLog parseia log de chat no formato IRC da Twitch
func ParseChatLog(source []byte, metadata map[string]interface{}) (*models.Channel, error) {
	channel := &models.Channel{
		Name: metadata["channel_name"].(string),
		Chat: &models.ChatLog{
			Messages: make([]models.ChatMessage, 0),
		},
	}

	scanner := bufio.NewScanner(strings.NewReader(string(source)))
	lineNum := 0

	// Regex para parsear mensagens IRC da Twitch
	// Ex: @badge-info=;badges=;client-nonce=abc;color=#FF0000;display-name=User;... :User!User@User.tmi.twitch.tv PRIVMSG #channel :Hello!
	messageRe := regexp.MustCompile(`^@([^ ]+) :([^!]+)![^ ]+ PRIVMSG #([^ ]+) :(.+)$`)

	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())

		// Ignorar linhas vazias e PING/PONG
		if line == "" || strings.HasPrefix(line, "PING") || strings.HasPrefix(line, "PONG") {
			continue
		}

		matches := messageRe.FindStringSubmatch(line)
		if len(matches) != 5 {
			// Tentar parse como mensagem simples (fallback)
			if strings.Contains(line, "PRIVMSG") {
				parts := strings.SplitN(line, " :", 2)
				if len(parts) == 2 {
					msg := models.ChatMessage{
						RawLine:   line,
						Timestamp: time.Now(),
						Content:   parts[1],
						Valid:     true,
					}
					channel.Chat.Messages = append(channel.Chat.Messages, msg)
				}
			}
			continue
		}

		// Parse tags
		tags := parseIRCTags(matches[1])

		// Extrair campos
		username := matches[2]
		//channelName := matches[3]
		content := matches[4]

		// Parse timestamp se disponível
		var timestamp time.Time
		if tsStr, ok := tags["tmi-sent-ts"]; ok {
			if ts, err := strconv.ParseInt(tsStr, 10, 64); err == nil {
				timestamp = time.Unix(ts/1000, 0)
			}
		} else {
			timestamp = time.Now()
		}

		// Parse badges
		var badges []string
		if badgeStr, ok := tags["badges"]; ok && badgeStr != "" {
			for _, badge := range strings.Split(badgeStr, ",") {
				parts := strings.SplitN(badge, "/", 2)
				if len(parts) == 2 {
					badges = append(badges, parts[0]) // Nome do badge
				}
			}
		}

		// Parse color
		color := tags["color"]

		// Parse emotes
		var emotes []models.EmoteRef
		if emoteStr, ok := tags["emotes"]; ok && emoteStr != "" {
			emotes = parseEmotes(emoteStr, content)
		}

		// Detectar tipos especiais de mensagem
		msgType := detectMessageType(tags, content)

		// Criar mensagem
		msg := models.ChatMessage{
			ID:          fmt.Sprintf("%s_%d", username, timestamp.Unix()),
			Username:    username,
			DisplayName: tags["display-name"],
			Content:     content,
			Timestamp:   timestamp,
			Color:       color,
			Badges:      badges,
			Emotes:      emotes,
			MessageType: msgType,
			RawTags:     tags,
			Valid:       true,
		}

		// Detectar ações de moderação
		if msgType == models.MsgTypeTimeout || msgType == models.MsgTypeBan {
			channel.ModerationActions = append(channel.ModerationActions, models.ModerationAction{
				Type:      msgType,
				Target:    username,
				Timestamp: timestamp,
				Reason:    extractBanReason(content),
			})
		}

		channel.Chat.Messages = append(channel.Chat.Messages, msg)
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading chat log: %w", err)
	}

	// Calcular métricas básicas de chat
	channel.Chat.TotalMessages = len(channel.Chat.Messages)
	channel.Chat.UniqueUsers = countUniqueUsers(channel.Chat.Messages)
	channel.Chat.MsgsPerMinute = calculateMessagesPerMinute(channel.Chat.Messages)

	return channel, nil
}

// parseIRCTags parseia tags IRC no formato key=value;key2=value2
func parseIRCTags(tagStr string) map[string]string {
	tags := make(map[string]string)

	for _, tag := range strings.Split(tagStr, ";") {
		parts := strings.SplitN(tag, "=", 2)
		if len(parts) == 2 {
			tags[parts[0]] = parts[1]
		} else if len(parts) == 1 {
			tags[parts[0]] = ""
		}
	}

	return tags
}

// parseEmotes parseia string de emotes da Twitch
func parseEmotes(emoteStr, content string) []models.EmoteRef {
	var emotes []models.EmoteRef

	// Format: emote_id:first-last,another-first-last/emote_id2:first-last
	for _, emoteGroup := range strings.Split(emoteStr, "/") {
		parts := strings.SplitN(emoteGroup, ":", 2)
		if len(parts) != 2 {
			continue
		}

		emoteID := parts[0]

		for _, position := range strings.Split(parts[1], ",") {
			posParts := strings.Split(position, "-")
			if len(posParts) != 2 {
				continue
			}

			start, _ := strconv.Atoi(posParts[0])
			end, _ := strconv.Atoi(posParts[1])

			// Extrair texto do emote do conteúdo
			if start >= 0 && end < len(content) {
				emoteText := content[start : end+1]
				emotes = append(emotes, models.EmoteRef{
					ID:    emoteID,
					Text:  emoteText,
					Start: start,
					End:   end,
				})
			}
		}
	}

	return emotes
}

// detectMessageType classifica tipo de mensagem baseado em tags e conteúdo
func detectMessageType(tags map[string]string, content string) models.MessageType {
	// Verificar message-type tag
	if msgType, ok := tags["msg-id"]; ok {
		switch msgType {
		case "sub", "resub", "subgift", "submysterygift":
			return models.MsgTypeSubscription
		case "cheer":
			return models.MsgTypeCheer
		case "raid":
			return models.MsgTypeRaid
		case "ritual":
			return models.MsgTypeRitual
		case "timeout":
			return models.MsgTypeTimeout
		case "ban":
			return models.MsgTypeBan
		case "unmod", "mod":
			return models.MsgTypeModeration
		}
	}

	// Detectar comandos de bot
	if strings.HasPrefix(content, "!") {
		return models.MsgTypeCommand
	}

	// Detectar menções
	if strings.Contains(content, "@") {
		return models.MsgTypeMention
	}

	return models.MsgTypeChat
}

// extractBanReason extrai razão de ban/timeout da mensagem do sistema
func extractBanReason(content string) string {
	// Formato típico: "Username has been timed out for 600 seconds. Reason: spam"
	re := regexp.MustCompile(`Reason:\s*(.+)$`)
	if matches := re.FindStringSubmatch(content); len(matches) > 1 {
		return strings.TrimSpace(matches[1])
	}
	return ""
}

// countUniqueUsers conta usuários únicos em lista de mensagens
func countUniqueUsers(messages []models.ChatMessage) int {
	seen := make(map[string]bool)
	for _, msg := range messages {
		if msg.Username != "" {
			seen[msg.Username] = true
		}
	}
	return len(seen)
}

// calculateMessagesPerMinute calcula taxa de mensagens por minuto
func calculateMessagesPerMinute(messages []models.ChatMessage) float64 {
	if len(messages) < 2 {
		return 0
	}

	// Encontrar primeiro e último timestamp
	first := messages[0].Timestamp
	last := messages[len(messages)-1].Timestamp

	duration := last.Sub(first).Minutes()
	if duration <= 0 {
		return float64(len(messages))
	}

	return float64(len(messages)) / duration
}
