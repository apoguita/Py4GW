from lupa import LuaRuntime

# Initialize Lua
lua = LuaRuntime(unpack_returned_tuples=True)

# Run a simple Lua command
result = lua.eval("2 + 3 * 5")
print("Lua result:", result)  # Output should be: 17

# Define and execute a Lua function
lua_func = lua.eval("function(x, y) return x * y end")
print("Lua function result:", lua_func(6, 7))  # Output should be: 42
