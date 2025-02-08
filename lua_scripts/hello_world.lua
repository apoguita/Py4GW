
local MapIDTester = {}

function MapIDTester.render()
    PyImGui.begin("Lua Hello World")
    PyImGui.text("lua text")
    if PyImGui.button("Button") then
        print("Button pressed")
    end
    PyImGui["end"]()

end

return MapIDTester
