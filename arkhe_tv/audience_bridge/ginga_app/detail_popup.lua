--[[
  detail_popup.lua
  Painel de detalhes da audiência — exibido ao pressionar tecla azul.
]]

function show_details(broadcaster_id)
  -- Buscar dados completos da emissora
  local http = require("http")
  local url = API_BASE_URL .. "/" .. broadcaster_id

  local success, response = pcall(function()
    return http.request(url)
  end)

  if not success then
    canvas:attrColor(255, 255, 255, 255)
    canvas:drawText(10, 50, "Erro ao carregar dados de audiência")
    return
  end

  -- Parse JSON
  local json = require("json")
  local data = json.decode(response)

  -- Desenhar fundo do popup
  local popup_x = canvas:getWidth() * 0.60
  local popup_y = canvas:getHeight() * 0.10
  local popup_w = canvas:getWidth() * 0.35
  local popup_h = canvas:getHeight() * 0.80

  canvas:attrColor(0, 0, 0, 220)
  canvas:drawRect("fill", popup_x, popup_y, popup_w, popup_h)

  -- Título
  canvas:attrFont("Tiresias", 16, "bold")
  canvas:attrColor(255, 255, 255, 255)
  canvas:drawText(popup_x + 10, popup_y + 10,
    "📊 Audiência: " .. data.display_name)

  -- Total viewers
  canvas:attrFont("Tiresias", 24, "bold")
  canvas:attrColor(0, 255, 0, 255)
  canvas:drawText(popup_x + 10, popup_y + 50,
    "Total: " .. format_number(data.total_viewers) .. " viewers")

  -- Breakdown por plataforma
  canvas:attrFont("Tiresias", 14, "normal")
  local y = popup_y + 100

  for platform, count in pairs(data.platform_breakdown) do
    local icon = ""
    if platform == "twitch" then icon = "🎮"
    elseif platform == "youtube" then icon = "📺"
    elseif platform == "tiktok" then icon = "📱"
    end

    canvas:attrColor(255, 255, 255, 255)
    canvas:drawText(popup_x + 10, y,
      icon .. " " .. platform:upper() .. ": " .. format_number(count))
    y = y + 25
  end

  -- Canais ativos
  y = y + 20
  canvas:attrFont("Tiresias", 12, "bold")
  canvas:drawText(popup_x + 10, y, "Canais ao vivo:")

  for _, ch in ipairs(data.channels) do
    if ch.viewers > 0 then
      y = y + 20
      canvas:attrFont("Tiresias", 11, "normal")
      canvas:attrColor(200, 200, 200, 255)
      canvas:drawText(popup_x + 20, y,
        ch.channel .. " (" .. ch.platform .. "): " .. ch.viewers .. " viewers")
      if y > popup_y + popup_h - 40 then break end
    end
  end

  -- Φ_C e Selo Temporal
  y = popup_y + popup_h - 30
  canvas:attrFont("Tiresias", 10, "normal")
  canvas:attrColor(150, 150, 150, 255)
  canvas:drawText(popup_x + 10, y,
    "⚛️ Φ_C: " .. string.format("%.4f", data.phi_c_coherence))
  canvas:drawText(popup_x + 10, y + 15,
    "🔐 Selo: " .. string.sub(data.temporal_seal or "N/A", 1, 16) .. "...")
end

-- Expor função para o NCL
show_details(selected_broadcaster or "globo")
