package parsers

import (
    "encoding/json"
    "arkhe/parser/frontends/twitch/models"
)

func ParseChannelExport(source []byte) (*models.Channel, error) {
    var raw map[string]interface{}
    if err := json.Unmarshal(source, &raw); err != nil {
        return nil, err
    }

    channel := &models.Channel{}
    if chanData, ok := raw["channel"].(map[string]interface{}); ok {
        if id, ok := chanData["broadcaster_id"].(string); ok { channel.ID = id }
        if name, ok := chanData["broadcaster_login"].(string); ok { channel.Name = name }
        if disp, ok := chanData["display_name"].(string); ok { channel.DisplayName = disp }
        if count, ok := chanData["follower_count"].(float64); ok { channel.FollowerCount = int(count) }
    }

    return channel, nil
}

func ParseStreamMetrics(source []byte) (*models.Channel, error) {
    var raw map[string]interface{}
    if err := json.Unmarshal(source, &raw); err != nil {
        return nil, err
    }

    channel := &models.Channel{}
    if chanData, ok := raw["stream"].(map[string]interface{}); ok {
        if id, ok := chanData["id"].(string); ok { channel.ID = id }
    }
    return channel, nil
}

func ParseAPIResponse(source []byte) (*models.Channel, error) {
    var raw map[string]interface{}
    if err := json.Unmarshal(source, &raw); err != nil {
        return nil, err
    }

    channel := &models.Channel{}
    if chanData, ok := raw["channel"].(map[string]interface{}); ok {
        if name, ok := chanData["name"].(string); ok { channel.Name = name }
    }

    if revList, ok := raw["revenue"].([]interface{}); ok {
        var revenue []models.RevenueEntry
        for _, r := range revList {
            if rev, ok := r.(map[string]interface{}); ok {
                entry := models.RevenueEntry{}
                if t, ok := rev["type"].(string); ok { entry.Type = t }
                if amt, ok := rev["amount"].(float64); ok { entry.Amount = amt }
                if curr, ok := rev["currency"].(string); ok { entry.Currency = curr }
                revenue = append(revenue, entry)
            }
        }
        channel.Revenue = revenue
    }
    return channel, nil
}
