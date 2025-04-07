from Py4GWCoreLib import *

class Compass():
    overlay = PyOverlay.Overlay()
    window_module = ImGui.WindowModule('Compass+',window_name='Compass+',window_pos=(234,802),window_size=(300,10),
                                       window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

    class Position:
        snap_to_game = True
        always_point_north = False
        x = 200
        y = 200
        size = 400

    class Markers:
        class Size:
            default  = 6
            player   = 6
            boss     = 8
            minion   = 4
            signpost = 6
            item     = 6

        class Color:
            default     = Utils.RGBToColor(128, 128, 128, 255)
            player      = Utils.RGBToColor(255, 128,   0, 255)
            player_dead = Utils.RGBToColor(255, 128,   0, 100)
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

            bosses      = True
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

        class Shape: # circle, tear, square
            default  = 'Tear'
            player   = 'Tear'
            minion   = 'Tear'
            signpost = 'Square'
            item     = 'Square'

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
            'spirit'     : True,
            'compass'   : False
        }

        range = {
            'touch'     : Range.Touch.value,
            'adjacent'  : Range.Adjacent.value,
            'nearby'    : Range.Nearby.value,
            'area'      : Range.Area.value,
            'earshot'   : Range.Earshot.value,
            'spellcast' : Range.Spellcast.value,
            'spirit'     : Range.Spirit.value,
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
            'spirit'     : Utils.RGBToColor(255, 255 , 255, 255),
            'compass'   : Utils.RGBToColor(255, 255 , 255, 255)
        }
    
        outline_thickness = {
            'touch'     : 1.5,
            'adjacent'  : 1.5,
            'nearby'    : 1.5,
            'area'      : 1.5,
            'earshot'   : 1.5,
            'spellcast' : 1.5,
            'spirit'     : 1.5,
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

def GetOrientation():
    global compass

    frame_id = UIManager.GetFrameIDByHash(3268554015)
    if compass.position.snap_to_game and UIManager.FrameExists(frame_id):
        left,top,right,bottom = UIManager.GetFrameCoords(frame_id)
        height = bottom - top
        diff = height - (height/1.05)

        top    += diff
        left   += diff
        bottom -= diff
        right  -= diff

        compass_x = round((left + right)/2)
        compass_y = round(top + (right - left)/2)

        position = PyOverlay.Point2D(compass_x,compass_y)
        size = round((right-left)/2)

        if compass.position.always_point_north:
            rotation = math.radians(90)
        else:
            rotation = Camera.GetCurrentYaw()

        return position, size, rotation
    else:
        compass_x = round(compass.position.x + compass.position.size/2)
        compass_y = round(compass.position.y + compass.position.size/2)
        position = PyOverlay.Point2D(compass_x,compass_y)

        size = compass.position.size

        if compass.position.always_point_north:
            rotation = math.radians(90)
        else:
            rotation = Camera.GetCurrentYaw()

        return position, size, rotation

def DrawRangeRings(position, size):
    global compass

    rings = [key for key, value in compass.range_rings.show.items() if value]

    for ring in rings:
        range = compass.range_rings.range[ring]
        fill_col = compass.range_rings.fill_color[ring]
        outline_col = compass.range_rings.outline_color[ring]
        outline_thickness = compass.range_rings.outline_thickness[ring]

        compass.overlay.DrawPolyFilled(position, size*range/Range.Compass.value, numSegments=64, color = fill_col)
        compass.overlay.DrawPoly(position, size*range/Range.Compass.value, numSegments=64, color = outline_col, thickness=outline_thickness)

def DrawAgents(position, compass_size, rotation):
    global compass

    def rotate(origin, point, angle):
        angle -= math.pi/2
        ox, oy = origin
        px, py = point
        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return qx, qy

    def GetAgentParams(agent_id):
        # misc
        is_alive = Agent.IsAlive(agent_id)
        allegiance = Agent.GetAllegiance(agent_id)[0] 

        # player
        if agent_id == Player.GetAgentID():
            if is_alive:
                return (compass.markers.color.player, compass.markers.shape.player, compass.markers.size.player)
            
            return (compass.markers.color.player_dead, compass.markers.shape.player, compass.markers.size.player)
        
        # signpost
        if Agent.IsGadget(agent_id):
            return (compass.markers.color.signpost, compass.markers.shape.signpost, compass.markers.size.signpost)
        
        # item
        if Agent.IsItem(agent_id) or not Agent.IsLiving(agent_id):
            return (compass.markers.color.item, compass.markers.shape.item,compass.markers.size.item)
        
        # enemies
        if allegiance == Allegiance.Enemy.value:
            if not is_alive:
                return (compass.markers.color.enemy_dead, compass.markers.shape.default, compass.markers.size.default)
            
            if compass.markers.color.bosses and Agent.HasBossGlow(agent_id):
                return (compass.markers.color.profession[Agent.GetProfessionIDs(agent_id)[0]], compass.markers.shape.default, compass.markers.size.boss)
            
            return (compass.markers.color.enemy, compass.markers.shape.default, compass.markers.size.default)
        
        # neutral
        if allegiance == Allegiance.Neutral.value:
            return (compass.markers.color.neutral, compass.markers.shape.default, compass.markers.size.default)
        
        # npc
        if not is_alive:
            return (compass.markers.color.ally_dead, compass.markers.shape.default, compass.markers.size.default)
        
        match allegiance:
            case Allegiance.Ally.value:
                return (compass.markers.color.ally, compass.markers.shape.default, compass.markers.size.default)
            case Allegiance.NpcMinipet.value:
                return (compass.markers.color.ally_npc, compass.markers.shape.default, compass.markers.size.default)
            case Allegiance.SpiritPet.value:
                return (compass.markers.color.ally_spirit, compass.markers.shape.default, compass.markers.size.default)
            case Allegiance.Minion.value:
                return (compass.markers.color.ally_minion, compass.markers.shape.minion, compass.markers.size.minion)
        
        # default
        return (compass.markers.color.default, compass.markers.shape.default, compass.markers.size.default)

    map_center = Player.GetXY()
    for agent_id in AgentArray.GetAgentArray():
        if not Agent.IsValid(agent_id): continue
        col, shape, size = GetAgentParams(agent_id)

        coord = Agent.GetXY(agent_id)
        agent_x = position.x - (map_center[0] - coord[0])*compass_size/Range.Compass.value
        agent_y = position.y + (map_center[1] - coord[1])*compass_size/Range.Compass.value

        (x_,y_) = rotate((position.x,position.y),(agent_x,agent_y),rotation)

        outline_col = compass.markers.color.target if agent_id == Player.GetTargetID() else Utils.RGBToColor(0,0,0,255)
        outline_thickness = 3 if agent_id == Player.GetTargetID() else 1.5

        if shape == 'Circle':
            pos = PyOverlay.Point2D(round(x_), round(y_))

            compass.overlay.DrawPolyFilled(pos, size, numSegments=64, color = col)
            compass.overlay.DrawPoly(pos, size, numSegments=64, color = outline_col, thickness=outline_thickness)
        else:
            

            scale = [1,1,1,1]
            if shape == 'Tear':
                scale = [2,1,1,1]
            elif shape == 'Square':
                scale = [1,1,1,1]

            rot = -Agent.GetRotationAngle(agent_id) - math.radians(90) + rotation
            p1 = PyOverlay.Point2D(round(math.cos(rot)*scale[0]*size + x_), round(math.sin(rot)*scale[0]*size + y_))
            rot += math.radians(90)
            p2 = PyOverlay.Point2D(round(math.cos(rot)*scale[1]*size + x_), round(math.sin(rot)*scale[1]*size + y_))
            rot += math.radians(90)
            p3 = PyOverlay.Point2D(round(math.cos(rot)*scale[2]*size + x_), round(math.sin(rot)*scale[2]*size + y_))
            rot += math.radians(90)
            p4 = PyOverlay.Point2D(round(math.cos(rot)*scale[3]*size + x_), round(math.sin(rot)*scale[3]*size + y_))

            compass.overlay.DrawQuadFilled(p1, p2, p3, p4, color = col)
            compass.overlay.DrawQuad(p1, p2, p3, p4, color = outline_col, thickness = outline_thickness)

def DrawCompass():
    global compass

    compass.overlay.BeginDraw()
    position, size, rotation = GetOrientation()
    DrawRangeRings(position, size)
    DrawAgents(position, size, rotation)
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
                compass.position.always_point_north = PyImGui.checkbox('Always Point North', compass.position.always_point_north)
                compass.position.x     = PyImGui.slider_int('X Position',   compass.position.x,    0, 2500)
                compass.position.y     = PyImGui.slider_int('Y Position',   compass.position.y,    0, 1800)
                compass.position.size  = PyImGui.slider_int('Compass Size', compass.position.size, 100, 1000)

            # agent settings
            if PyImGui.collapsing_header(f'Agents'):
                if PyImGui.tree_node('Color'):
                    compass.markers.color.default     = Utils.TupleToColor(PyImGui.color_edit4('Default',            Utils.ColorToTuple(compass.markers.color.default)))
                    compass.markers.color.player      = Utils.TupleToColor(PyImGui.color_edit4('Player',             Utils.ColorToTuple(compass.markers.color.player)))
                    compass.markers.color.player_dead = Utils.TupleToColor(PyImGui.color_edit4('Player Dead',        Utils.ColorToTuple(compass.markers.color.player_dead)))
                    compass.markers.color.ally        = Utils.TupleToColor(PyImGui.color_edit4('Ally',               Utils.ColorToTuple(compass.markers.color.ally)))
                    compass.markers.color.ally_npc    = Utils.TupleToColor(PyImGui.color_edit4('Ally NPC',           Utils.ColorToTuple(compass.markers.color.ally_npc)))
                    compass.markers.color.ally_spirit = Utils.TupleToColor(PyImGui.color_edit4('Ally Spirit',        Utils.ColorToTuple(compass.markers.color.ally_spirit)))
                    compass.markers.color.ally_minion = Utils.TupleToColor(PyImGui.color_edit4('Ally Minion',        Utils.ColorToTuple(compass.markers.color.ally_minion)))
                    compass.markers.color.ally_dead   = Utils.TupleToColor(PyImGui.color_edit4('Ally Dead',          Utils.ColorToTuple(compass.markers.color.ally_dead)))
                    compass.markers.color.neutral     = Utils.TupleToColor(PyImGui.color_edit4('Neutral',            Utils.ColorToTuple(compass.markers.color.neutral)))
                    compass.markers.color.enemy       = Utils.TupleToColor(PyImGui.color_edit4('Enemy',              Utils.ColorToTuple(compass.markers.color.enemy)))
                    compass.markers.color.enemy_dead  = Utils.TupleToColor(PyImGui.color_edit4('Enemy Dead',         Utils.ColorToTuple(compass.markers.color.enemy_dead)))
                    compass.markers.color.item        = Utils.TupleToColor(PyImGui.color_edit4('Item',               Utils.ColorToTuple(compass.markers.color.item)))
                    compass.markers.color.signpost    = Utils.TupleToColor(PyImGui.color_edit4('Signpost',           Utils.ColorToTuple(compass.markers.color.signpost)))
                    compass.markers.color.eoe         = Utils.TupleToColor(PyImGui.color_edit4('Edge of Extinction', Utils.ColorToTuple(compass.markers.color.eoe)))
                    compass.markers.color.qz          = Utils.TupleToColor(PyImGui.color_edit4('Quickening Zepher',  Utils.ColorToTuple(compass.markers.color.qz)))
                    compass.markers.color.winnowing   = Utils.TupleToColor(PyImGui.color_edit4('Winnowing',          Utils.ColorToTuple(compass.markers.color.winnowing)))
                    PyImGui.tree_pop()
                if PyImGui.tree_node('Size'):
                    compass.markers.size.default  = PyImGui.slider_int('Default',  compass.markers.size.default,  1, 10)
                    compass.markers.size.player   = PyImGui.slider_int('Player',   compass.markers.size.player,   1, 10)
                    compass.markers.size.boss     = PyImGui.slider_int('Boss',     compass.markers.size.boss,     1, 10)
                    compass.markers.size.minion   = PyImGui.slider_int('Minion',   compass.markers.size.minion,   1, 10)
                    compass.markers.size.signpost = PyImGui.slider_int('Signpost', compass.markers.size.signpost, 1, 10)
                    compass.markers.size.item     = PyImGui.slider_int('Item',     compass.markers.size.item,     1, 10)
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
                if PyImGui.tree_node('Visible'):
                    for ring in compass.range_rings.show.keys():
                        compass.range_rings.show[ring] = PyImGui.checkbox(ring.capitalize(), compass.range_rings.show[ring])
                    PyImGui.tree_pop()
                if PyImGui.tree_node('Fill Color'):
                    for ring in compass.range_rings.show.keys():
                        compass.range_rings.fill_color[ring] = Utils.TupleToColor(PyImGui.color_edit4(ring.capitalize(), Utils.ColorToTuple(compass.range_rings.fill_color[ring])))
                    PyImGui.tree_pop()
                if PyImGui.tree_node('Line Color'):
                    for ring in compass.range_rings.show.keys():
                        compass.range_rings.outline_color[ring] = Utils.TupleToColor(PyImGui.color_edit4(ring.capitalize(), Utils.ColorToTuple(compass.range_rings.outline_color[ring])))
                    PyImGui.tree_pop()
                if PyImGui.tree_node('Line Thickness'):
                    for ring in compass.range_rings.show.keys():
                        compass.range_rings.outline_thickness[ring] = PyImGui.slider_float(ring.capitalize(), compass.range_rings.outline_thickness[ring], 0, 5)
                    PyImGui.tree_pop()

            PyImGui.pop_style_color(11)
        PyImGui.end()

    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name # type: ignore
        Py4GW.Console.Log('BOT', f'Error in {current_function}: {str(e)}', Py4GW.Console.MessageType.Error)
        raise

def main():
    try:
        if Map.IsMapReady() and Party.IsPartyLoaded() and not UIManager.IsWorldMapShowing():
            DrawConfig()
            DrawCompass()

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