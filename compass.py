from Py4GWCoreLib import *

class Compass():
    overlay = PyOverlay.Overlay()
    window_module = ImGui.WindowModule('Compass+',window_name='Compass+',window_pos=(1200,400),window_size=(300,10),
                                       window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
    player_id = 0
    target_id = 0

    class Position:
        snap_to_game = True
        always_point_north = False

        player_pos = (1.0,1.0)

        snapped_pos = PyOverlay.Point2D(1,1)
        snapped_size = 1

        display_size = PyOverlay.Overlay().GetDisplaySize()
        detached_pos = PyOverlay.Point2D(round(display_size.x/2),round(display_size.y/2))
        detached_size = 500

        current_pos = PyOverlay.Point2D(1,1)
        current_size = 500

        rotation = 0.0

    class Markers:
        class Size:
            default  = 6
            player   = 6
            boss     = 8
            minion   = 4
            signpost = 5
            item     = 5

        class Color:
            default     = Utils.RGBToColor(128, 128, 128, 255)
            player      = Utils.RGBToColor(255, 128,   0, 255)
            player_dead = Utils.RGBToColor(255, 128,   0, 100)
            players     = Utils.RGBToColor(100, 100, 255, 255)
            players_dead = Utils.RGBToColor(100, 100, 255, 100)
            ally        = Utils.RGBToColor(  0, 179,   0, 255) 
            ally_npc    = Utils.RGBToColor(153, 255, 153, 255)
            ally_spirit = Utils.RGBToColor( 96, 128,   0, 255)
            ally_minion = Utils.RGBToColor(  0, 128,  96, 255)
            ally_dead   = Utils.RGBToColor(  0, 100,   0, 100)
            neutral     = Utils.RGBToColor(  0,   0, 220, 255)
            enemy       = Utils.RGBToColor(240,   0,   0, 255)
            enemy_dead  = Utils.RGBToColor( 50,   0,   0, 255)
            item        = Utils.RGBToColor(  0,   0, 240, 255)
            signpost    = Utils.RGBToColor(  0,   0, 200, 255)
            eoe         = Utils.RGBToColor(  0, 255,   0,  50)
            qz          = Utils.RGBToColor(  0,   0, 255,  50)
            winnowing   = Utils.RGBToColor(  0, 255 ,255,  50)

            target      = Utils.RGBToColor(255, 255 ,  0, 255)

            profession = [Utils.RGBToColor(102, 102, 102, 255),
                          Utils.RGBToColor(238, 170,  51, 255),
                          Utils.RGBToColor( 85, 170,   0, 255),
                          Utils.RGBToColor( 68,  68, 187, 255),
                          Utils.RGBToColor(  0, 170,  85, 255),
                          Utils.RGBToColor(136,   0, 170, 255),
                          Utils.RGBToColor(187,  51,  51, 255),
                          Utils.RGBToColor(170,   0, 136, 255),
                          Utils.RGBToColor(  0, 170, 170, 255),
                          Utils.RGBToColor(153, 102,   0, 255),
                          Utils.RGBToColor(119, 119, 204, 255)]

        class Shape: # Circle, Tear, Square
            default  = 'Tear'
            player   = 'Tear'
            minion   = 'Tear'
            signpost = 'Circle'
            item     = 'Circle'

        size  = Size()
        color = Color()
        shape = Shape()

    class RangeRings:
        show = {
            'touch'     : False,
            'adjacent'  : False,
            'nearby'    : False,
            'area'      : False,
            'earshot'   : True,
            'spellcast' : True,
            'spirit'    : True,
            'compass'   : False
        }

        range = {
            'touch'     : Range.Touch.value,
            'adjacent'  : Range.Adjacent.value,
            'nearby'    : Range.Nearby.value,
            'area'      : Range.Area.value,
            'earshot'   : Range.Earshot.value,
            'spellcast' : Range.Spellcast.value,
            'spirit'    : Range.Spirit.value,
            'compass'   : Range.Compass.value
        }

        fill_color = {
            'touch'     : Utils.RGBToColor(255, 255 , 255, 0),
            'adjacent'  : Utils.RGBToColor(255, 255 , 255, 0),
            'nearby'    : Utils.RGBToColor(255, 255 , 255, 0),
            'area'      : Utils.RGBToColor(255, 255 , 255, 0),
            'earshot'   : Utils.RGBToColor(255, 255 , 255, 0),
            'spellcast' : Utils.RGBToColor(255, 255 , 255, 0),
            'spirit'    : Utils.RGBToColor(255, 255 , 255, 0),
            'compass'   : Utils.RGBToColor(255, 255 , 255, 0)
        }

        outline_color = {
            'touch'     : Utils.RGBToColor(255, 255 , 255, 255),
            'adjacent'  : Utils.RGBToColor(255, 255 , 255, 255),
            'nearby'    : Utils.RGBToColor(255, 255 , 255, 255),
            'area'      : Utils.RGBToColor(255, 255 , 255, 255),
            'earshot'   : Utils.RGBToColor(255, 255 , 255, 255),
            'spellcast' : Utils.RGBToColor(255, 255 , 255, 255),
            'spirit'    : Utils.RGBToColor(255, 255 , 255, 255),
            'compass'   : Utils.RGBToColor(255, 255 , 255, 255)
        }
    
        outline_thickness = {
            'touch'     : 1.5,
            'adjacent'  : 1.5,
            'nearby'    : 1.5,
            'area'      : 1.5,
            'earshot'   : 1.5,
            'spellcast' : 1.5,
            'spirit'    : 1.5,
            'compass'   : 1.5
        }
     
    position = Position()
    markers = Markers()
    range_rings = RangeRings()

compass = Compass()

def Debug(message, title = 'DEBUG', msg_type = 'Debug'):
    py4gw_msg_type = Py4GW.Console.MessageType.Debug
    if   msg_type == 'Debug':       py4gw_msg_type = Py4GW.Console.MessageType.Debug
    elif msg_type == 'Error':       py4gw_msg_type = Py4GW.Console.MessageType.Error
    elif msg_type == 'Info':        py4gw_msg_type = Py4GW.Console.MessageType.Info
    elif msg_type == 'Notice':      py4gw_msg_type = Py4GW.Console.MessageType.Notice
    elif msg_type == 'Performance': py4gw_msg_type = Py4GW.Console.MessageType.Performance
    elif msg_type == 'Success':     py4gw_msg_type = Py4GW.Console.MessageType.Success
    elif msg_type == 'Warning':     py4gw_msg_type = Py4GW.Console.MessageType.Warning
    Py4GW.Console.Log(title, str(message), py4gw_msg_type)

def UpdateTarget():
    global compass
    compass.target_id = Player.GetTargetID()

def UpdateOrientation():
    global compass

    compass.position.player_pos = Player.GetXY()
    if compass.position.snap_to_game and Map.MiniMap.FrameExists():
        left,top,right,bottom = Map.MiniMap.GetCoords()
        height = bottom - top
        diff = height - (height/1.05)

        top    += diff
        left   += diff
        bottom -= diff
        right  -= diff

        compass_x = round((left + right)/2)
        compass_y = round(top + (right - left)/2)

        compass.position.snapped_pos = PyOverlay.Point2D(compass_x,compass_y)
        compass.position.snapped_size = round((right-left)/2)

        compass.position.current_pos = compass.position.snapped_pos
        compass.position.current_size = compass.position.snapped_size
    else:
        compass.position.current_pos = compass.position.detached_pos
        compass.position.current_size = compass.position.detached_size

    if Map.MiniMap.IsLocked() or (not compass.position.snap_to_game and compass.position.always_point_north):
        compass.position.rotation = math.radians(90)
    else:
        compass.position.rotation = Camera.GetCurrentYaw()

def DrawRangeRings():
    global compass

    rings = [key for key, value in compass.range_rings.show.items() if value]

    for ring in rings:
        range = compass.range_rings.range[ring]
        fill_col = compass.range_rings.fill_color[ring]
        outline_col = compass.range_rings.outline_color[ring]
        outline_thickness = compass.range_rings.outline_thickness[ring]

        compass.overlay.DrawPolyFilled(compass.position.current_pos, compass.position.current_size*range/Range.Compass.value, numSegments=64, color = fill_col)
        compass.overlay.DrawPoly(compass.position.current_pos, compass.position.current_size*range/Range.Compass.value, numSegments=64, color = outline_col, thickness=outline_thickness)

def DrawAgent(agent_id, shape, size, col, is_spirit = False):
    agent_pos = Agent.GetXY(agent_id)
    agent_x = compass.position.current_pos.x - (compass.position.player_pos[0] - agent_pos[0])*compass.position.current_size/Range.Compass.value
    agent_y = compass.position.current_pos.y + (compass.position.player_pos[1] - agent_pos[1])*compass.position.current_size/Range.Compass.value

    camera_rotation = compass.position.rotation - math.pi/2
    x = compass.position.current_pos.x + math.cos(camera_rotation) * (agent_x - compass.position.current_pos.x) - math.sin(camera_rotation) * (agent_y - compass.position.current_pos.y)
    y = compass.position.current_pos.y + math.sin(camera_rotation) * (agent_x - compass.position.current_pos.x) + math.cos(camera_rotation) * (agent_y - compass.position.current_pos.y)

    line_col = Utils.RGBToColor(255,255,0,255) if agent_id == compass.target_id else Utils.RGBToColor(0,0,0,255)
    line_thickness = 3 if agent_id == compass.target_id else 1.5
    if shape == 'Circle':
        pos = PyOverlay.Point2D(round(x), round(y))

        compass.overlay.DrawPolyFilled(pos, size, numSegments=64, color = col)
        compass.overlay.DrawPoly(pos, size, numSegments=64, color = line_col, thickness=line_thickness)

        if is_spirit:
            match Agent.GetPlayerNumber(agent_id):
                case 2875:
                    compass.overlay.DrawPolyFilled(pos, compass.position.current_size*Range.Spirit.value/Range.Compass.value, numSegments=64, color = compass.markers.color.winnowing)
                case 2876:
                    compass.overlay.DrawPolyFilled(pos, compass.position.current_size*Range.Spirit.value/Range.Compass.value, numSegments=64, color = compass.markers.color.eoe)
                case 2886:
                    compass.overlay.DrawPolyFilled(pos, compass.position.current_size*Range.Spirit.value/Range.Compass.value, numSegments=64, color = compass.markers.color.qz)
    else:
        scale = [1,1,1,1]
        if shape == 'Tear':
            scale = [2,1,1,1]
        elif shape == 'Square':
            scale = [1,1,1,1]

        rot = -Agent.GetRotationAngle(agent_id) - math.radians(90) + compass.position.rotation
        p1 = PyOverlay.Point2D(round(math.cos(rot)*scale[0]*size + x), round(math.sin(rot)*scale[0]*size + y))
        rot += math.radians(90)
        p2 = PyOverlay.Point2D(round(math.cos(rot)*scale[1]*size + x), round(math.sin(rot)*scale[1]*size + y))
        rot += math.radians(90)
        p3 = PyOverlay.Point2D(round(math.cos(rot)*scale[2]*size + x), round(math.sin(rot)*scale[2]*size + y))
        rot += math.radians(90)
        p4 = PyOverlay.Point2D(round(math.cos(rot)*scale[3]*size + x), round(math.sin(rot)*scale[3]*size + y))

        compass.overlay.DrawQuadFilled(p1, p2, p3, p4, color = col)
        compass.overlay.DrawQuad(p1, p2, p3, p4, color = line_col, thickness = line_thickness)

def DrawAgents():
    global compass

    for agent_id in AgentArray.GetAllyArray():
        alive = Agent.IsAlive(agent_id)
        if Agent.IsNPC(agent_id):
            if alive:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally)
            else:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally_dead)
        elif agent_id == compass.player_id:
            if alive:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.player, compass.markers.color.player)
            else:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.player, compass.markers.color.player_dead)
        else:
            if alive:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.players)
            else:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.players_dead)

    for agent_id in AgentArray.GetNPCMinipetArray():
        if Agent.IsAlive(agent_id):
            DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally_npc)
        else:
            DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally_dead)

    for agent_id in AgentArray.GetSpiritPetArray():
        alive = Agent.IsAlive(agent_id)
        if Agent.IsSpirit(agent_id):
            if alive:
                DrawAgent(agent_id, 'Circle', compass.markers.size.default, compass.markers.color.ally_spirit, is_spirit = True)
        else:
            if alive: 
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally_spirit)
            else:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally_dead)

    for agent_id in AgentArray.GetMinionArray():
        if Agent.IsAlive(agent_id):
            DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.minion, compass.markers.color.ally_minion)
        else:
            DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.minion, compass.markers.color.ally_dead)

    for agent_id in AgentArray.GetNeutralArray():
        DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.neutral)

    for agent_id in AgentArray.GetEnemyArray():
        alive = Agent.IsAlive(agent_id)
        if Agent.HasBossGlow(agent_id):
            if alive:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.boss, compass.markers.color.profession[Agent.GetProfessionIDs(agent_id)[0]])
            else:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.boss, compass.markers.color.enemy_dead)
        else:
            if alive:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.enemy)
            else:
                DrawAgent(agent_id, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.enemy_dead)

    for agent_id in AgentArray.GetItemArray():
        DrawAgent(agent_id, compass.markers.shape.item, compass.markers.size.item, compass.markers.color.item)

    for agent_id in AgentArray.GetGadgetArray():
        DrawAgent(agent_id, compass.markers.shape.signpost, compass.markers.size.signpost, compass.markers.color.signpost)

def DrawCompass():
    global compass

    UpdateOrientation()
    compass.overlay.BeginDraw()
    DrawRangeRings()
    DrawAgents()
    compass.overlay.EndDraw()

def DrawConfig():
    global compass

    if compass.window_module.first_run:
        PyImGui.set_next_window_size(compass.window_module.window_size[0], compass.window_module.window_size[1])     
        PyImGui.set_next_window_pos(compass.window_module.window_pos[0], compass.window_module.window_pos[1])
        compass.window_module.first_run = False

    try:
        if PyImGui.begin(compass.window_module.window_name, compass.window_module.window_flags):
            # style/color
            PyImGui.push_style_color(PyImGui.ImGuiCol.Header,           (.2,.2,.2,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered,    (.3,.3,.3,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive,     (.4,.4,.4,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg,          (0.2, 0.2, 0.2, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered,   (0.3, 0.3, 0.3, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive,    (0.4, 0.4, 0.4, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab,       (0.0, 0.0, 0.0, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, (0.0, 0.0, 0.0, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,           (0.2, 0.2, 0.2, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered,    (0.3, 0.3, 0.3, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,     (0.4, 0.4, 0.4, 1))

            # position settings
            if PyImGui.collapsing_header(f'Position'):
                compass.position.snap_to_game = PyImGui.checkbox('Snap To Game Compass', compass.position.snap_to_game)
                if not compass.position.snap_to_game:
                    compass.position.always_point_north = PyImGui.checkbox('Always Point North', compass.position.always_point_north)
                    x = PyImGui.slider_int('X Position', compass.position.detached_pos.x, compass.position.current_size, round(compass.position.display_size.x - compass.position.current_size))
                    y = PyImGui.slider_int('Y Position', compass.position.detached_pos.y, compass.position.current_size, round(compass.position.display_size.y - compass.position.current_size))
                    compass.position.detached_pos = PyOverlay.Point2D(x,y)
                    compass.position.detached_size = PyImGui.slider_int('Scale', compass.position.detached_size, 100, 1000)

            # agent settings
            if PyImGui.collapsing_header(f'Agents'):
                if PyImGui.tree_node('Color'):
                    compass.markers.color.default      = Utils.TupleToColor(PyImGui.color_edit4('Default',            Utils.ColorToTuple(compass.markers.color.default)))
                    compass.markers.color.player       = Utils.TupleToColor(PyImGui.color_edit4('Player',             Utils.ColorToTuple(compass.markers.color.player)))
                    compass.markers.color.player_dead  = Utils.TupleToColor(PyImGui.color_edit4('Player Dead',        Utils.ColorToTuple(compass.markers.color.player_dead)))
                    compass.markers.color.players      = Utils.TupleToColor(PyImGui.color_edit4('Other Players',      Utils.ColorToTuple(compass.markers.color.players)))
                    compass.markers.color.players_dead = Utils.TupleToColor(PyImGui.color_edit4('Other Players Dead', Utils.ColorToTuple(compass.markers.color.players_dead)))
                    compass.markers.color.ally         = Utils.TupleToColor(PyImGui.color_edit4('Ally',               Utils.ColorToTuple(compass.markers.color.ally)))
                    compass.markers.color.ally_npc     = Utils.TupleToColor(PyImGui.color_edit4('Ally NPC',           Utils.ColorToTuple(compass.markers.color.ally_npc)))
                    compass.markers.color.ally_spirit  = Utils.TupleToColor(PyImGui.color_edit4('Ally Spirit',        Utils.ColorToTuple(compass.markers.color.ally_spirit)))
                    compass.markers.color.ally_minion  = Utils.TupleToColor(PyImGui.color_edit4('Ally Minion',        Utils.ColorToTuple(compass.markers.color.ally_minion)))
                    compass.markers.color.ally_dead    = Utils.TupleToColor(PyImGui.color_edit4('Ally Dead',          Utils.ColorToTuple(compass.markers.color.ally_dead)))
                    compass.markers.color.neutral      = Utils.TupleToColor(PyImGui.color_edit4('Neutral',            Utils.ColorToTuple(compass.markers.color.neutral)))
                    compass.markers.color.enemy        = Utils.TupleToColor(PyImGui.color_edit4('Enemy',              Utils.ColorToTuple(compass.markers.color.enemy)))
                    compass.markers.color.enemy_dead   = Utils.TupleToColor(PyImGui.color_edit4('Enemy Dead',         Utils.ColorToTuple(compass.markers.color.enemy_dead)))
                    compass.markers.color.item         = Utils.TupleToColor(PyImGui.color_edit4('Item',               Utils.ColorToTuple(compass.markers.color.item)))
                    compass.markers.color.signpost     = Utils.TupleToColor(PyImGui.color_edit4('Signpost',           Utils.ColorToTuple(compass.markers.color.signpost)))
                    compass.markers.color.eoe          = Utils.TupleToColor(PyImGui.color_edit4('Edge of Extinction', Utils.ColorToTuple(compass.markers.color.eoe)))
                    compass.markers.color.qz           = Utils.TupleToColor(PyImGui.color_edit4('Quickening Zepher',  Utils.ColorToTuple(compass.markers.color.qz)))
                    compass.markers.color.winnowing    = Utils.TupleToColor(PyImGui.color_edit4('Winnowing',          Utils.ColorToTuple(compass.markers.color.winnowing)))
                    PyImGui.tree_pop()
                if PyImGui.tree_node('Size'):
                    compass.markers.size.default  = PyImGui.slider_int('Default',  compass.markers.size.default,  1, 20)
                    compass.markers.size.player   = PyImGui.slider_int('Player',   compass.markers.size.player,   1, 20)
                    compass.markers.size.boss     = PyImGui.slider_int('Boss',     compass.markers.size.boss,     1, 20)
                    compass.markers.size.minion   = PyImGui.slider_int('Minion',   compass.markers.size.minion,   1, 20)
                    compass.markers.size.signpost = PyImGui.slider_int('Signpost', compass.markers.size.signpost, 1, 20)
                    compass.markers.size.item     = PyImGui.slider_int('Item',     compass.markers.size.item,     1, 20)
                    PyImGui.tree_pop()
                if PyImGui.tree_node('Shape'):
                    items = ['Circle','Tear', 'Square']
                    compass.markers.shape.default  = items[PyImGui.combo('Default',  items.index(compass.markers.shape.default),  items)]
                    compass.markers.shape.player   = items[PyImGui.combo('Player',   items.index(compass.markers.shape.player),   items)]
                    compass.markers.shape.minion   = items[PyImGui.combo('Minion',   items.index(compass.markers.shape.minion),   items)]
                    compass.markers.shape.signpost = items[PyImGui.combo('Signpost', items.index(compass.markers.shape.signpost), items)]
                    compass.markers.shape.item     = items[PyImGui.combo('Item',     items.index(compass.markers.shape.item),     items)]
                    PyImGui.tree_pop()

            # range ring settings
            if PyImGui.collapsing_header(f'Range Rings'):
                for ring in compass.range_rings.show.keys():
                    if PyImGui.tree_node(ring.capitalize()):
                        compass.range_rings.show[ring] = PyImGui.checkbox('Visible', compass.range_rings.show[ring])
                        compass.range_rings.fill_color[ring] = Utils.TupleToColor(PyImGui.color_edit4('Fill Color', Utils.ColorToTuple(compass.range_rings.fill_color[ring])))
                        compass.range_rings.outline_color[ring] = Utils.TupleToColor(PyImGui.color_edit4('Line Color', Utils.ColorToTuple(compass.range_rings.outline_color[ring])))
                        compass.range_rings.outline_thickness[ring] = PyImGui.slider_float('Line Thickness', compass.range_rings.outline_thickness[ring], 0, 5)
                        PyImGui.tree_pop()

            PyImGui.pop_style_color(11)
        PyImGui.end()

    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name # type: ignore
        Py4GW.Console.Log('BOT', f'Error in {current_function}: {str(e)}', Py4GW.Console.MessageType.Error)
        raise

action_queue = ActionQueueManager()
def main():
    global compass, action_queue
    try:
        if Map.IsMapLoading():
            compass.player_id = 0

        if Map.IsMapReady() and Party.IsPartyLoaded() and not UIManager.IsWorldMapShowing():
            DrawConfig()
            DrawCompass()

            if action_queue.IsEmpty('ACTION'):
                action_queue.AddAction('ACTION',UpdateTarget)
            else:
                action_queue.ProcessQueue('ACTION')

            if not compass.player_id:
                compass.player_id = Player.GetAgentID()

    except ImportError as e:
        Py4GW.Console.Log('Compass', f'ImportError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log('Compass', f'ValueError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log('Compass', f'TypeError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log('Compass', f'Unexpected error encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == '__main__':
    main()