-- imgui.lua
local imgui = {}

function imgui.begin(title) 
    return PyImGui.begin(title)
end

function imgui.end_window() 
    return PyImGui.end_()
end

function imgui.text(text) 
    return PyImGui.text(text)
end

return imgui
