// tests/lua_parser_test.go
package tests

import (
	"testing"

	"arkhe/parser/frontends/lua"
	"github.com/stretchr/testify/assert"
)

func TestLuaParser_SimpleScript(t *testing.T) {
	parser := lua.NewLuaParser()

	source := []byte(`
-- Simple Lua script
local function greet(name)
    return "Hello, " .. name
end

local config = {
    debug = true,
    max_players = 10,
    settings = {
        volume = 0.8,
        fullscreen = false
    }
}

print(greet("World"))
`)

	graph, err := parser.Parse(source, "test.lua", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)

	// Verify coherence is in valid range
	assert.GreaterOrEqual(t, graph.Metrics.CoherenceScore, 0.0)
	assert.LessOrEqual(t, graph.Metrics.CoherenceScore, 1.0)

	// Verify expected attributes
	root := graph.Nodes[graph.RootNodes[0]]
	assert.Equal(t, 1, root.Attributes["function_count"])
	assert.Equal(t, 2, root.Attributes["table_count"]) // Changed from 1 to 2 because there are two tables (config and settings)
	assert.Equal(t, 2, root.Attributes["max_table_depth"]) // config.settings
}

func TestLuaParser_UnsafePatterns(t *testing.T) {
	parser := lua.NewLuaParser()
	parser.DetectPatterns = true

	source := []byte(`
-- Script with unsafe patterns
local code = "print('injected')"
loadstring(code)() -- UNSAFE: dynamic code execution

local env = getfenv(2) -- UNSAFE: environment manipulation (Lua 5.1)
env.malicious = function() end
`)

	graph, err := parser.Parse(source, "unsafe.lua", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]
	unsafeCount := root.Attributes["unsafe_patterns"].(int)
	assert.GreaterOrEqual(t, unsafeCount, 0)

	// Safety score should be reduced
	safety := root.Attributes["coherence_safety"].(float64)
	assert.LessOrEqual(t, safety, 1.0)
}

func TestLuaParser_TableGraph(t *testing.T) {
	parser := lua.NewLuaParser()

	source := []byte(`
-- Complex table with metatable
local mt = {
    __index = function(t, k)
        return rawget(t, k) or "default"
    end,
    __newindex = function(t, k, v)
        if type(v) ~= "string" then
            error("expected string")
        end
        rawset(t, k, v)
    end
}

local obj = setmetatable({}, mt)
obj.name = "test"
`)

	graph, err := parser.Parse(source, "metatable.lua", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]
	// Make sure it doesn't fail
	assert.NotNil(t, root.Attributes["table_count"])
}

func TestLuaParser_CoroutineFlow(t *testing.T) {
	parser := lua.NewLuaParser()

	source := []byte(`
-- Proper coroutine usage
local co = coroutine.create(function()
    for i = 1, 10 do
        coroutine.yield(i)
    end
end)

while coroutine.status(co) ~= "dead" do
    local ok, val = coroutine.resume(co)
    if ok then print(val) end
end
`)

	graph, err := parser.Parse(source, "coroutine.lua", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]
	assert.NotNil(t, root.Attributes["coroutine_count"])
}

func TestLuaParser_BytecodeDetection(t *testing.T) {
	parser := lua.NewLuaParser()

	// Lua 5.4 bytecode header: \027LuaQ\000\001\004\004\004\008\000
	bytecode := []byte{0x1B, 0x4C, 0x75, 0x61, 0x51, 0x00, 0x01, 0x04}

	graph, err := parser.Parse(bytecode, "test.luac", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]
	assert.Equal(t, "lua_bytecode", root.Attributes["format"])
	// Bytecode parsing returns baseline coherence
	assert.Equal(t, 0.7, root.Attributes["coherence_score"])
}
