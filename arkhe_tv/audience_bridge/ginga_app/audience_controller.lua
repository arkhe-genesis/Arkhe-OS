--[[
  audience_controller.lua
  Script Lua (NCLua) para consulta de audiência via HTTP e exibição na TV 3.0.

  Compatível com: Ginga-NCL perfil D, TV 3.0/DTV+, nclua-http
  Backend: ARKHE Audience Bridge API
]]

-- Configuração
local API_BASE_URL = "http://192.168.1.100:8054/api/v1/audience"
local POLL_INTERVAL_MS = 60000  -- 60 segundos

-- Mapeamento de emissoras
local broadcasters = {"globo", "sbt", "record", "band", "cultura"}
local viewer_counts = {globo = 0, sbt = 0, record = 0, band = 0, cultura = 0}
local total_viewers = 0

-- ============================================================================
-- Função: Consultar audiência de uma emissora via HTTP
-- ============================================================================
function fetch_audience(broadcaster_id)
  -- Usar módulo nclua-http para requisição HTTP
  -- https://github.com/manoelcampos/nclua-http
  local http = require("http")
  local json = require("json")  -- Se disponível; senão, parse manual

  local url = API_BASE_URL .. "/" .. broadcaster_id .. "/simple"

  local success, response = pcall(function()
    return http.request(url)
  end)

  if success and response then
    -- Parsear JSON da resposta
    -- Resposta esperada: {"v": 12345, "tw": 8000, "yt": 4000, "tk": 345, "ts": 1715712000}
    local ok, data = pcall(function()
      if json then
        return json.decode(response)
      else
        -- Parse manual simplificado
        local v = string.match(response, '"v":(%d+)')
        local tw = string.match(response, '"tw":(%d+)')
        local yt = string.match(response, '"yt":(%d+)')
        local tk = string.match(response, '"tk":(%d+)')
        return {
          v = tonumber(v) or 0,
          tw = tonumber(tw) or 0,
          yt = tonumber(yt) or 0,
          tk = tonumber(tk) or 0,
        }
      end
    end)

    if ok and data then
      return data
    end
  end

  -- Fallback: retornar zeros em caso de erro
  return {v = 0, tw = 0, yt = 0, tk = 0}
end

-- ============================================================================
-- Função: Atualizar todos os contadores de audiência
-- ============================================================================
function update_all_audiences()
  local new_total = 0

  for _, bid in ipairs(broadcasters) do
    local data = fetch_audience(bid)
    viewer_counts[bid] = data.v
    new_total = new_total + data.v
  end

  total_viewers = new_total

  -- Atualizar propriedades NCL (para exibição nos textos)
  -- As propriedades são mapeadas no documento NCL:
  --   globoViewers, sbtViewers, recordViewers, bandViewers, culturaViewers
  canvas:draw()

  -- Registrar atualização no log do Ginga (se disponível)
  if event then
    event.post({
      class = "ncl",
      type = "attribution",
      name = "audience_updated",
      value = tostring(total_viewers),
    })
  end
end

-- ============================================================================
-- Função: Desenhar barra de audiência na tela
-- ============================================================================
function draw_audience_bar()
  -- Cores por emissora
  local colors = {
    globo   = {r = 0.0, g = 0.5, b = 1.0},   -- Azul
    sbt     = {r = 0.0, g = 0.8, b = 0.0},   -- Verde
    record  = {r = 1.0, g = 0.0, b = 0.0},   -- Vermelho
    band    = {r = 1.0, g = 0.6, b = 0.0},   -- Laranja
    cultura = {r = 0.0, g = 0.8, b = 0.8},   -- Ciano
  }

  local bar_width = canvas:getWidth()
  local bar_height = canvas:getHeight() * 0.10  -- 10% da altura da tela
  local y = canvas:getHeight() - bar_height

  -- Fundo semi-transparente
  canvas:attrColor(0, 0, 0, 180)
  canvas:drawRect("fill", 0, y, bar_width, bar_height)

  -- Desenhar cada emissora proporcionalmente
  local x = 0
  local segment_width = bar_width / #broadcasters

  for _, bid in ipairs(broadcasters) do
    local color = colors[bid]
    canvas:attrColor(color.r * 255, color.g * 255, color.b * 255, 255)
    canvas:drawRect("fill", x, y, segment_width - 2, bar_height)

    -- Texto: nome da emissora + viewer count
    canvas:attrFont("Tiresias", 12, "bold")
    canvas:attrColor(255, 255, 255, 255)

    local text = string.format("%s: %s",
      bid:sub(1,1):upper()..bid:sub(2),
      format_number(viewer_counts[bid])
    )
    canvas:drawText(x + 5, y + bar_height/2 - 8, text)

    x = x + segment_width
  end
end

-- ============================================================================
-- Função: Formatar número com sufixo (K, M)
-- ============================================================================
function format_number(n)
  if n >= 1000000 then
    return string.format("%.1fM", n / 1000000)
  elseif n >= 1000 then
    return string.format("%.1fK", n / 1000)
  else
    return tostring(n)
  end
end

-- ============================================================================
-- Função: Abrir link do Twitch (segunda tela)
-- ============================================================================
function open_twitch_link(broadcaster_id)
  local twitch_urls = {
    globo   = "https://www.twitch.tv/tvglobo",
    sbt     = "https://www.twitch.tv/sbt",
    record  = "https://www.twitch.tv/recordtv",
    band    = "https://www.twitch.tv/bandtv",
    cultura = "https://www.twitch.tv/tvcultura",
  }

  local url = twitch_urls[broadcaster_id]
  if url then
    -- No Ginga-NCL DTV Play, podemos usar a API de segunda tela
    -- ou abrir o link via WebSocket para dispositivo móvel
    if second_screen then
      second_screen.open(url)
    else
      -- Fallback: mostrar QR code ou URL na tela
      canvas:attrColor(255, 255, 255, 255)
      canvas:drawText(10, canvas:getHeight() - 50,
        "Twitch: " .. url)
    end
  end
end

-- ============================================================================
-- Função: Handler de teclas do controle remoto
-- ============================================================================
function handler(evt)
  if evt.class == "key" then
    if evt.type == "press" then
      if evt.key == "BLUE" then
        -- Tecla azul: mostrar/esconder painel de detalhes
        show_detail_panel = not show_detail_panel
      elseif evt.key == "RED" then
        -- Tecla vermelha: abrir Twitch da emissora em foco
        local focused_index = get_focused_broadcaster()
        if focused_index then
          open_twitch_link(broadcasters[focused_index])
        end
      elseif evt.key == "CURSOR_LEFT" then
        focus_index = ((focus_index - 2) % #broadcasters) + 1
      elseif evt.key == "CURSOR_RIGHT" then
        focus_index = (focus_index % #broadcasters) + 1
      elseif evt.key == "ENTER" then
        -- Abrir detalhes da emissora em foco
        selected_broadcaster = broadcasters[focus_index]
        show_detail_panel = true
      end
    end
  end
end

-- ============================================================================
-- Inicialização da aplicação
-- ============================================================================
function init()
  print("[ARKHE] Audience App iniciado para TV 3.0/DTV+")
  print("[ARKHE] Backend: " .. API_BASE_URL)

  -- Registrar handler de eventos
  event.register(handler)

  -- Primeira consulta imediata
  update_all_audiences()

  -- Configurar timer para atualização periódica
  -- Em Ginga-NCL, o timer é gerenciado via NCL (onTimer)
  -- Aqui, usamos o loop de eventos do Lua
  local last_update = os.time()

  -- Loop principal (executado via scheduler do Ginga)
  while true do
    local now = os.time()
    if now - last_update >= 60 then
      update_all_audiences()
      last_update = now
    end
    -- Redesenhar barra
    draw_audience_bar()
    -- Aguardar próximo frame (30fps → ~33ms)
    socket.sleep(0.033)
  end
end

-- Iniciar aplicação
init()
