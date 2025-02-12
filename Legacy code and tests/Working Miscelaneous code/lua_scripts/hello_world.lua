
local MapIDTester = {}

function MapIDTester.render()
    PyImGui.begin("Lua Hello World")
    PyImGui.text("lua text")
    if PyImGui.button("Button") then
        print("Button pressed")
    end
    local player_id = Player.GetAgentID()
    PyImGui.text("Player ID: " .. player_id)
    local player_name = Agent.GetName(player_id)
    PyImGui.text("Player Name: " .. player_name)
    PyImGui.separator()
    local map_id = Map.GetMapID()
    PyImGui.text("Map ID: " .. map_id)
    local map_name = Map.GetMapName(map_id)
    PyImGui.text("Map Name: " .. map_name)
    local players_in_instance = Map.GetAmountOfPlayersInInstance()
    PyImGui.text("Players in instance: " .. players_in_instance)

    PyImGui["end"]()

end

return MapIDTester
