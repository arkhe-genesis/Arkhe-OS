-- examples/lua/game_entity.lua
-- Entity component system in Lua (coherent example)

local Entity = {}
Entity.__index = Entity

-- Well-documented metamethods with clear contracts
function Entity:new(config)
    local self = setmetatable({}, Entity)
    self.id = config.id or math.random(10000)
    self.components = {}
    self.active = true
    return self
end

function Entity:addComponent(name, component)
    -- Type check for safety
    if type(component) ~= "table" then
        error("component must be a table")
    end
    self.components[name] = component
    component.entity = self -- Back-reference
end

function Entity:update(dt)
    for _, comp in pairs(self.components) do
        if comp.update then
            comp:update(dt)
        end
    end
end

-- Safe metamethod: __tostring for debugging
function Entity:__tostring()
    return string.format("Entity[%d](active=%s)", self.id, tostring(self.active))
end

-- Avoid unsafe patterns: no loadstring, no global pollution
return Entity
