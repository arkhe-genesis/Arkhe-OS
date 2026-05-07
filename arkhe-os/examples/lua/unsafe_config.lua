-- examples/lua/unsafe_config.lua
-- Example with anti-patterns (for testing safety detection)

-- UNSAFE: Dynamic code execution
local user_input = "os.execute('rm -rf /')"
loadstring(user_input)() -- ⚠️ Dangerous!

-- UNSAFE: Global variable pollution
globalConfig = { debug = true } -- Should be local

-- UNSAFE: Environment manipulation (Lua 5.1 style)
local old_env = getfenv(2)
setfenv(2, { print = function() end }) -- Silences output

-- Better approach (commented):
-- local config = { debug = true }
-- return config
