-- map_id_tester.lua
local imgui = require("imgui")

local MapIDTester = {}
MapIDTester.__index = MapIDTester

function MapIDTester.new()
    local self = setmetatable({}, MapIDTester)
    self.title = "MapID Tester"
    self.log = "Hello World"
    self.map_id = 0
    return self
end

function MapIDTester:render()
    imgui.Begin(self.title)
    
    -- Display log
    imgui.Text("Log:")
    imgui.Text(self.log)
    
    -- Display button to test MapID
    if imgui.Button("Test MapID") then
        -- Call the MapID function
        self.map_id = map.GetMapID()
        self.log = "MapID: " .. tostring(self.map_id)
    end
    
    -- Display current MapID
    if self.map_id then
        imgui.Text("Current MapID: " .. tostring(self.map_id))
    end
    
    imgui.End()
end

return MapIDTester
