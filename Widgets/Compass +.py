from Py4GWCoreLib import *

class Compass():
    window_module = ImGui.WindowModule('Compass+',window_name='Compass+', window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
    window_pos = (1200,400)
    ini = IniHandler(os.path.join(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")), "Widgets/Config/Compass +.ini"))
    initialized = False
    ini_timer = Timer()

    overlay = PyOverlay.Overlay()
    renderer = DXOverlay()

    reset      = True
    frame_id   = 0
    player_id  = 0
    target_id  = 0
    geometry   = []
    map_bounds = []

    class Position:
        snap_to_game = True
        always_point_north = False
        buffer = 10
        culling = 4365

        player_pos = (1.0,1.0)

        snapped_pos = PyOverlay.Point2D(1,1)
        snapped_size = 1

        display_size = PyOverlay.Overlay().GetDisplaySize()
        detached_pos = PyOverlay.Point2D(round(display_size.x/2),round(display_size.y/2))
        detached_size = 400

        current_pos = PyOverlay.Point2D(1,1)
        current_size = 400

        rotation = 0.0

    class Markers:
        class Size:
            default  = 6
            player   = 6
            boss     = 7
            minion   = 3
            signpost = 5
            item     = 5

        class Color:
            default      = Utils.RGBToColor(128, 128, 128, 255)
            player       = Utils.RGBToColor(255, 128,   0, 255)
            player_dead  = Utils.RGBToColor(255, 128,   0, 100)
            players      = Utils.RGBToColor(100, 100, 255, 255)
            players_dead = Utils.RGBToColor(100, 100, 255, 100)
            ally         = Utils.RGBToColor(  0, 179,   0, 255) 
            ally_npc     = Utils.RGBToColor(153, 255, 153, 255)
            ally_spirit  = Utils.RGBToColor( 96, 128,   0, 255)
            ally_minion  = Utils.RGBToColor(  0, 128,  96, 255)
            ally_dead    = Utils.RGBToColor(  0, 100,   0, 100)
            neutral      = Utils.RGBToColor(  0,   0, 220, 255)
            enemy        = Utils.RGBToColor(240,   0,   0, 255)
            enemy_dead   = Utils.RGBToColor( 50,   0,   0, 255)
            item         = Utils.RGBToColor(255, 255,   0, 255)
            signpost     = Utils.RGBToColor(120, 120, 120, 255)
            eoe          = Utils.RGBToColor(  0, 255,   0,  50)
            qz           = Utils.RGBToColor(  0,   0, 255,  50)
            winnowing    = Utils.RGBToColor(  0, 255 ,255,  50)

            target       = Utils.RGBToColor(255, 255 ,  0, 255)

            profession  = [Utils.RGBToColor(102, 102, 102, 255),
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
    
    class Pathing:
        show = True
        color = Utils.RGBToColor(255, 255, 255, 80)

    def Reset(self):
        self.reset      = False
        self.frame_id   = Map.MiniMap.GetFrameID()
        self.player_id  = Player.GetAgentID()
        self.geometry   = Map.Pathing.GetComputedGeometry()
        self.map_bounds = list(Map.GetMapBoundaries())

    def LoadConfig(self):
        self.initialized = True

        self.window_pos = (self.ini.read_int('Compass+',  'config_x', self.window_pos[0]),
                           self.ini.read_int('Compass+',  'config_y', self.window_pos[1]))

        self.position.snap_to_game       = self.ini.read_bool('Compass+', 'snap_to_game',       self.position.snap_to_game)
        self.position.always_point_north = self.ini.read_bool('Compass+', 'always_point_north', self.position.always_point_north)
        self.position.culling            = self.ini.read_int('Compass+',  'culling',            self.position.culling)
        self.position.detached_pos = PyOverlay.Point2D(
                                           self.ini.read_int('Compass+',  'detached_x',         self.position.detached_pos.x),
                                           self.ini.read_int('Compass+',  'detached_y',         self.position.detached_pos.y))
        self.position.detached_size      = self.ini.read_int('Compass+',  'detached_size',      self.position.detached_size)

        self.markers.size.default  = self.ini.read_int('Compass+', 'default_size',  self.markers.size.default)
        self.markers.size.player   = self.ini.read_int('Compass+', 'player_size',   self.markers.size.player)
        self.markers.size.boss     = self.ini.read_int('Compass+', 'boss_size',     self.markers.size.boss)
        self.markers.size.minion   = self.ini.read_int('Compass+', 'minion_size',   self.markers.size.minion)
        self.markers.size.signpost = self.ini.read_int('Compass+', 'signpost_size', self.markers.size.signpost)
        self.markers.size.item     = self.ini.read_int('Compass+', 'item_size',     self.markers.size.item)

        self.markers.color.default      = self.ini.read_int('Compass+',  'default_color',      self.markers.color.default)
        self.markers.color.player       = self.ini.read_int('Compass+',  'player_color',       self.markers.color.player)
        self.markers.color.player_dead  = self.ini.read_int('Compass+',  'player_dead_color',  self.markers.color.player_dead)
        self.markers.color.players      = self.ini.read_int('Compass+',  'players_color',      self.markers.color.players)
        self.markers.color.players_dead = self.ini.read_int('Compass+',  'players_dead_color', self.markers.color.players_dead)
        self.markers.color.ally         = self.ini.read_int('Compass+',  'ally_color',         self.markers.color.ally)
        self.markers.color.ally_npc     = self.ini.read_int('Compass+',  'ally_npc_color',     self.markers.color.ally_npc)
        self.markers.color.ally_spirit  = self.ini.read_int('Compass+',  'ally_spirit_color',  self.markers.color.ally_spirit)
        self.markers.color.ally_minion  = self.ini.read_int('Compass+',  'ally_minion_color',  self.markers.color.ally_minion)
        self.markers.color.ally_dead    = self.ini.read_int('Compass+',  'ally_dead_color',    self.markers.color.ally_dead)
        self.markers.color.neutral      = self.ini.read_int('Compass+',  'neutral_color',      self.markers.color.neutral)
        self.markers.color.enemy        = self.ini.read_int('Compass+',  'enemy_color',        self.markers.color.enemy)
        self.markers.color.enemy_dead   = self.ini.read_int('Compass+',  'enemy_dead_color',   self.markers.color.enemy_dead)
        self.markers.color.item         = self.ini.read_int('Compass+',  'item_color',         self.markers.color.item)
        self.markers.color.signpost     = self.ini.read_int('Compass+',  'signpost_color',     self.markers.color.signpost)
        self.markers.color.eoe          = self.ini.read_int('Compass+',  'eoe_color',          self.markers.color.eoe)
        self.markers.color.qz           = self.ini.read_int('Compass+',  'qz_color',           self.markers.color.qz)
        self.markers.color.winnowing    = self.ini.read_int('Compass+',  'winnowing_color',    self.markers.color.winnowing)

        self.markers.shape.default  = self.ini.read_key('Compass+', 'default_shape',  self.markers.shape.default)
        self.markers.shape.player   = self.ini.read_key('Compass+', 'player_shape',   self.markers.shape.player)
        self.markers.shape.minion   = self.ini.read_key('Compass+', 'minion_shape',   self.markers.shape.minion)
        self.markers.shape.signpost = self.ini.read_key('Compass+', 'signpost_shape', self.markers.shape.signpost)
        self.markers.shape.item     = self.ini.read_key('Compass+', 'item_shape',     self.markers.shape.item)

        self.range_rings.show['touch']     = self.ini.read_bool('Compass+', 'touch_show',     self.range_rings.show['touch'])
        self.range_rings.show['adjacent']  = self.ini.read_bool('Compass+', 'adjacent_show',  self.range_rings.show['adjacent'])
        self.range_rings.show['nearby']    = self.ini.read_bool('Compass+', 'nearby_show',    self.range_rings.show['nearby'])
        self.range_rings.show['area']      = self.ini.read_bool('Compass+', 'area_show',      self.range_rings.show['area'])
        self.range_rings.show['earshot']   = self.ini.read_bool('Compass+', 'earshot_show',   self.range_rings.show['earshot'])
        self.range_rings.show['spellcast'] = self.ini.read_bool('Compass+', 'spellcast_show', self.range_rings.show['spellcast'])
        self.range_rings.show['spirit']    = self.ini.read_bool('Compass+', 'spirit_show',    self.range_rings.show['spirit'])
        self.range_rings.show['compass']   = self.ini.read_bool('Compass+', 'compass_show',   self.range_rings.show['compass'])

        self.range_rings.fill_color['touch']     = self.ini.read_int('Compass+', 'touch_fill',     self.range_rings.fill_color['touch'])
        self.range_rings.fill_color['adjacent']  = self.ini.read_int('Compass+', 'adjacent_fill',  self.range_rings.fill_color['adjacent'])
        self.range_rings.fill_color['nearby']    = self.ini.read_int('Compass+', 'nearby_fill',    self.range_rings.fill_color['nearby'])
        self.range_rings.fill_color['area']      = self.ini.read_int('Compass+', 'area_fill',      self.range_rings.fill_color['area'])
        self.range_rings.fill_color['earshot']   = self.ini.read_int('Compass+', 'earshot_fill',   self.range_rings.fill_color['earshot'])
        self.range_rings.fill_color['spellcast'] = self.ini.read_int('Compass+', 'spellcast_fill', self.range_rings.fill_color['spellcast'])
        self.range_rings.fill_color['spirit']    = self.ini.read_int('Compass+', 'spirit_fill',    self.range_rings.fill_color['spirit'])
        self.range_rings.fill_color['compass']   = self.ini.read_int('Compass+', 'compass_fill',   self.range_rings.fill_color['compass'])

        self.range_rings.outline_color['touch']     = self.ini.read_int('Compass+', 'touch_outline',     self.range_rings.outline_color['touch'])
        self.range_rings.outline_color['adjacent']  = self.ini.read_int('Compass+', 'adjacent_outline',  self.range_rings.outline_color['adjacent'])
        self.range_rings.outline_color['nearby']    = self.ini.read_int('Compass+', 'nearby_outline',    self.range_rings.outline_color['nearby'])
        self.range_rings.outline_color['area']      = self.ini.read_int('Compass+', 'area_outline',      self.range_rings.outline_color['area'])
        self.range_rings.outline_color['earshot']   = self.ini.read_int('Compass+', 'earshot_outline',   self.range_rings.outline_color['earshot'])
        self.range_rings.outline_color['spellcast'] = self.ini.read_int('Compass+', 'spellcast_outline', self.range_rings.outline_color['spellcast'])
        self.range_rings.outline_color['spirit']    = self.ini.read_int('Compass+', 'spirit_outline',    self.range_rings.outline_color['spirit'])
        self.range_rings.outline_color['compass']   = self.ini.read_int('Compass+', 'compass_outline',   self.range_rings.outline_color['compass'])

        self.range_rings.outline_thickness['touch']     = self.ini.read_float('Compass+', 'touch_thickness',     self.range_rings.outline_thickness['touch'])
        self.range_rings.outline_thickness['adjacent']  = self.ini.read_float('Compass+', 'adjacent_thickness',  self.range_rings.outline_thickness['adjacent'])
        self.range_rings.outline_thickness['nearby']    = self.ini.read_float('Compass+', 'nearby_thickness',    self.range_rings.outline_thickness['nearby'])
        self.range_rings.outline_thickness['area']      = self.ini.read_float('Compass+', 'area_thickness',      self.range_rings.outline_thickness['area'])
        self.range_rings.outline_thickness['earshot']   = self.ini.read_float('Compass+', 'earshot_thickness',   self.range_rings.outline_thickness['earshot'])
        self.range_rings.outline_thickness['spellcast'] = self.ini.read_float('Compass+', 'spellcast_thickness', self.range_rings.outline_thickness['spellcast'])
        self.range_rings.outline_thickness['spirit']    = self.ini.read_float('Compass+', 'spirit_thickness',    self.range_rings.outline_thickness['spirit'])
        self.range_rings.outline_thickness['compass']   = self.ini.read_float('Compass+', 'compass_thickness',   self.range_rings.outline_thickness['compass'])

        self.pathing.show  = self.ini.read_bool('Compass+', 'pathin_show',  self.pathing.show)
        self.pathing.color = self.ini.read_int('Compass+',  'pathing_color', self.pathing.color)

    def SaveConfig(self):
        if not self.ini_timer.IsRunning():
            self.ini_timer.Start()

        if not self.ini_timer.HasElapsed(1000): return
        self.ini_timer.Reset()

        self.ini.write_key('Compass+', 'snap_to_game',        str(self.position.snap_to_game))
        self.ini.write_key('Compass+', 'always_point_north',  str(self.position.always_point_north))
        self.ini.write_key('Compass+', 'culling',             str(self.position.culling))
        self.ini.write_key('Compass+', 'detached_x',          str(self.position.detached_pos.x))
        self.ini.write_key('Compass+', 'detached_y',          str(self.position.detached_pos.y))
        self.ini.write_key('Compass+', 'detached_size',       str(self.position.detached_size))

        self.ini.write_key('Compass+', 'default_size',        str(self.markers.size.default))
        self.ini.write_key('Compass+', 'player_size',         str(self.markers.size.player))
        self.ini.write_key('Compass+', 'boss_size',           str(self.markers.size.boss))
        self.ini.write_key('Compass+', 'minion_size',         str(self.markers.size.minion))
        self.ini.write_key('Compass+', 'signpost_size',       str(self.markers.size.signpost))
        self.ini.write_key('Compass+', 'item_size',           str(self.markers.size.item))

        self.ini.write_key('Compass+',  'default_color',      str(self.markers.color.default))
        self.ini.write_key('Compass+',  'player_color',       str(self.markers.color.player))
        self.ini.write_key('Compass+',  'player_dead_color',  str(self.markers.color.player_dead))
        self.ini.write_key('Compass+',  'players_color',      str(self.markers.color.players))
        self.ini.write_key('Compass+',  'players_dead_color', str(self.markers.color.players_dead))
        self.ini.write_key('Compass+',  'ally_color',         str(self.markers.color.ally))
        self.ini.write_key('Compass+',  'ally_npc_color',     str(self.markers.color.ally_npc))
        self.ini.write_key('Compass+',  'ally_spirit_color',  str(self.markers.color.ally_spirit))
        self.ini.write_key('Compass+',  'ally_minion_color',  str(self.markers.color.ally_minion))
        self.ini.write_key('Compass+',  'ally_dead_color',    str(self.markers.color.ally_dead))
        self.ini.write_key('Compass+',  'neutral_color',      str(self.markers.color.neutral))
        self.ini.write_key('Compass+',  'enemy_color',        str(self.markers.color.enemy))
        self.ini.write_key('Compass+',  'enemy_dead_color',   str(self.markers.color.enemy_dead))
        self.ini.write_key('Compass+',  'item_color',         str(self.markers.color.item))
        self.ini.write_key('Compass+',  'signpost_color',     str(self.markers.color.signpost))
        self.ini.write_key('Compass+',  'eoe_color',          str(self.markers.color.eoe))
        self.ini.write_key('Compass+',  'qz_color',           str(self.markers.color.qz))
        self.ini.write_key('Compass+',  'winnowing_color',    str(self.markers.color.winnowing))

        self.ini.write_key('Compass+', 'default_shape',       str(self.markers.shape.default))
        self.ini.write_key('Compass+', 'player_shape',        str(self.markers.shape.player))
        self.ini.write_key('Compass+', 'minion_shape',        str(self.markers.shape.minion))
        self.ini.write_key('Compass+', 'signpost_shape',      str(self.markers.shape.signpost))
        self.ini.write_key('Compass+', 'item_shape',          str(self.markers.shape.item))

        self.ini.write_key('Compass+', 'touch_show',          str(self.range_rings.show['touch']))
        self.ini.write_key('Compass+', 'adjacent_show',       str(self.range_rings.show['adjacent']))
        self.ini.write_key('Compass+', 'nearby_show',         str(self.range_rings.show['nearby']))
        self.ini.write_key('Compass+', 'area_show',           str(self.range_rings.show['area']))
        self.ini.write_key('Compass+', 'earshot_show',        str(self.range_rings.show['earshot']))
        self.ini.write_key('Compass+', 'spellcast_show',      str(self.range_rings.show['spellcast']))
        self.ini.write_key('Compass+', 'spirit_show',         str(self.range_rings.show['spirit']))
        self.ini.write_key('Compass+', 'compass_show',        str(self.range_rings.show['compass']))

        self.ini.write_key('Compass+', 'touch_fill',          str(self.range_rings.fill_color['touch']))
        self.ini.write_key('Compass+', 'adjacent_fill',       str(self.range_rings.fill_color['adjacent']))
        self.ini.write_key('Compass+', 'nearby_fill',         str(self.range_rings.fill_color['nearby']))
        self.ini.write_key('Compass+', 'area_fill',           str(self.range_rings.fill_color['area']))
        self.ini.write_key('Compass+', 'earshot_fill',        str(self.range_rings.fill_color['earshot']))
        self.ini.write_key('Compass+', 'spellcast_fill',      str(self.range_rings.fill_color['spellcast']))
        self.ini.write_key('Compass+', 'spirit_fill',         str(self.range_rings.fill_color['spirit']))
        self.ini.write_key('Compass+', 'compass_fill',        str(self.range_rings.fill_color['compass']))

        self.ini.write_key('Compass+', 'touch_outline',       str(self.range_rings.outline_color['touch']))
        self.ini.write_key('Compass+', 'adjacent_outline',    str(self.range_rings.outline_color['adjacent']))
        self.ini.write_key('Compass+', 'nearby_outline',      str(self.range_rings.outline_color['nearby']))
        self.ini.write_key('Compass+', 'area_outline',        str(self.range_rings.outline_color['area']))
        self.ini.write_key('Compass+', 'earshot_outline',     str(self.range_rings.outline_color['earshot']))
        self.ini.write_key('Compass+', 'spellcast_outline',   str(self.range_rings.outline_color['spellcast']))
        self.ini.write_key('Compass+', 'spirit_outline',      str(self.range_rings.outline_color['spirit']))
        self.ini.write_key('Compass+', 'compass_outline',     str(self.range_rings.outline_color['compass']))

        self.ini.write_key('Compass+', 'touch_thickness',     str(self.range_rings.outline_thickness['touch']))
        self.ini.write_key('Compass+', 'adjacent_thickness',  str(self.range_rings.outline_thickness['adjacent']))
        self.ini.write_key('Compass+', 'nearby_thickness',    str(self.range_rings.outline_thickness['nearby']))
        self.ini.write_key('Compass+', 'area_thickness',      str(self.range_rings.outline_thickness['area']))
        self.ini.write_key('Compass+', 'earshot_thickness',   str(self.range_rings.outline_thickness['earshot']))
        self.ini.write_key('Compass+', 'spellcast_thickness', str(self.range_rings.outline_thickness['spellcast']))
        self.ini.write_key('Compass+', 'spirit_thickness',    str(self.range_rings.outline_thickness['spirit']))
        self.ini.write_key('Compass+', 'compass_thickness',   str(self.range_rings.outline_thickness['compass']))

        self.ini.write_key('Compass+', 'pathin_show',         str(self.pathing.show))
        self.ini.write_key('Compass+', 'pathing_color',       str(self.pathing.color))

    position    = Position()
    markers     = Markers()
    range_rings = RangeRings()
    pathing     = Pathing()

compass = Compass()
action_queue = ActionQueueManager()

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

def CheckCompassClick():
    if PyImGui.is_mouse_clicked(0): 
        if PyImGui.get_io().key_ctrl:
            pos = compass.overlay.GetMouseCoords()
            mouse_pos = (pos.x, pos.y)
            world_pos = Map.MiniMap.MapProjection.ScreenToGamePos(*mouse_pos,
                                                                  *compass.position.player_pos,
                                                                  compass.position.current_pos.x, compass.position.current_pos.y,
                                                                  compass.position.current_size, 
                                                                  compass.position.rotation)

            agent_array = AgentArray.GetAgentArray()
            agent_array = AgentArray.Sort.ByDistance(agent_array, world_pos)
            if len(agent_array) > 0:
                Player.ChangeTarget(agent_array[0])

        if PyImGui.get_io().key_alt:
            pos = compass.overlay.GetMouseCoords()
            mouse_pos = (pos.x, pos.y)

            world_pos = Map.MiniMap.MapProjection.ScreenToGamePos(*mouse_pos,
                                                                  *compass.position.player_pos,
                                                                  compass.position.current_pos.x, compass.position.current_pos.y,
                                                                  compass.position.current_size, 
                                                                  compass.position.rotation)
            Player.Move(*world_pos)

def UpdateOrientation():
    global compass

    compass.position.player_pos = Player.GetXY()

    if compass.position.snap_to_game and UIManager.FrameExists(compass.frame_id) and UIManager.IsWindowVisible(WindowID.WindowID_Compass):
        coords = UIManager.GetFrameCoords(compass.frame_id)

        compass_x, compass_y = Map.MiniMap.GetMapScreenCenter(coords)
        compass_x = round(compass_x)
        compass_y = round(compass_y)

        compass.position.snapped_pos = PyOverlay.Point2D(compass_x,compass_y)
        compass.position.snapped_size = round(Map.MiniMap.GetScale(coords))

        compass.position.current_pos = compass.position.snapped_pos
        compass.position.current_size = compass.position.snapped_size
    else:
        compass.position.current_pos = compass.position.detached_pos
        compass.position.current_size = compass.position.detached_size

    if compass.position.snap_to_game:
        compass.position.rotation = Map.MiniMap.GetRotation()
    else:
        if compass.position.always_point_north:
            compass.position.rotation = 0
        else:
            compass.position.rotation = Camera.GetCurrentYaw() - math.pi/2

def DrawRangeRings():
    global compass

    rings = [key for key, value in compass.range_rings.show.items() if value]

    for ring in rings:
        range = compass.range_rings.range[ring]
        fill_col = compass.range_rings.fill_color[ring]
        outline_col = compass.range_rings.outline_color[ring]
        outline_thickness = compass.range_rings.outline_thickness[ring]


        PyImGui.draw_list_add_circle(compass.position.current_pos.x,
                                     compass.position.current_pos.y,
                                     compass.position.current_size*range/Range.Compass.value,
                                     outline_col,
                                     64,
                                     outline_thickness)
        
        PyImGui.draw_list_add_circle_filled(compass.position.current_pos.x,
                                            compass.position.current_pos.y,
                                            compass.position.current_size*range/Range.Compass.value,
                                            fill_col,
                                            64)

def DrawAgent(x, y, rot, shape, size, col, target, spirit_col = None):
    global compass

    line_col = Utils.RGBToColor(255,255,0,255) if target else Utils.RGBToColor(0,0,0,255)
    line_thickness = 3 if target else 1.5

    if spirit_col:
        PyImGui.draw_list_add_circle_filled(x, y, compass.position.current_size*Range.Spirit.value/Range.Compass.value, spirit_col, 32)

    if shape == 'Circle':
        PyImGui.draw_list_add_circle_filled(x, y, size, col, 12)
        PyImGui.draw_list_add_circle(x, y, size, line_col, 12, line_thickness)
    else:
        scale = [1,1,1,1]
        if shape == 'Tear':
            scale = [2,1,1,1]
        elif shape == 'Square':
            scale = [1,1,1,1]
        
        x1 = math.cos(rot)*scale[0]*size + x
        y1 = math.sin(rot)*scale[0]*size + y
        rot += math.radians(90)
        x2 = math.cos(rot)*scale[1]*size + x
        y2 = math.sin(rot)*scale[1]*size + y
        rot += math.radians(90)
        x3 = math.cos(rot)*scale[2]*size + x
        y3 = math.sin(rot)*scale[2]*size + y
        rot += math.radians(90)
        x4 = math.cos(rot)*scale[3]*size + x
        y4 = math.sin(rot)*scale[3]*size + y

        PyImGui.draw_list_add_quad_filled(x1, y1, x2, y2, x3, y3, x4, y4, col)
        PyImGui.draw_list_add_quad(x1, y1, x2, y2, x3, y3, x4, y4, line_col, line_thickness)

def DrawAgents():
    global compass

    for agent in AgentArray.GetRawAgentArray():
        if not agent.id:
            continue
        
        if Utils.Distance((agent.x, agent.y), compass.position.player_pos) > compass.position.culling:
            continue

        x, y = Map.MiniMap.MapProjection.GamePosToScreen(agent.x, agent.y, *compass.position.player_pos,
                                                         compass.position.current_pos.x, compass.position.current_pos.y,
                                                         compass.position.current_size, compass.position.rotation)
        rot = compass.position.rotation - agent.rotation_angle
        is_target = agent.id == compass.target_id
        alive = agent.living_agent.is_alive

        match agent.living_agent.allegiance.ToInt():
            case Allegiance.Neutral:
                DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.neutral, is_target)
            case Allegiance.SpiritPet:
                if alive:
                    match agent.living_agent.player_number:
                        case 2875:
                            DrawAgent(x, y, rot, 'Circle', compass.markers.size.default, compass.markers.color.ally_spirit, is_target, spirit_col = compass.markers.color.winnowing)
                        case 2876:
                            DrawAgent(x, y, rot, 'Circle', compass.markers.size.default, compass.markers.color.ally_spirit, is_target, spirit_col = compass.markers.color.eoe)
                        case 2886:
                            DrawAgent(x, y, rot, 'Circle', compass.markers.size.default, compass.markers.color.ally_spirit, is_target, spirit_col = compass.markers.color.qz)
                        case _:
                            DrawAgent(x, y, rot, 'Circle', compass.markers.size.default, compass.markers.color.ally_spirit, is_target)
            case Allegiance.Minion:
                if alive:
                    DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.minion, compass.markers.color.ally_minion, is_target)
                else:
                    DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.minion, compass.markers.color.ally_dead, is_target)
            case Allegiance.NpcMinipet:
                if alive:
                    DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally_npc, is_target)
                else:
                    DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally_dead, is_target)
            case Allegiance.Ally:
                if agent.living_agent.is_npc:
                    if alive:
                        DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally, is_target)
                    else:
                        DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.ally_dead, is_target)
                elif agent.id == compass.player_id:
                    if alive:
                        DrawAgent(x, y, rot, compass.markers.shape.player, compass.markers.size.player, compass.markers.color.player, is_target)
                    else:
                        DrawAgent(x, y, rot, compass.markers.shape.player, compass.markers.size.player, compass.markers.color.player_dead, is_target)
                else:
                    if alive:
                        DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.players, is_target)
                    else:
                        DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.players_dead, is_target)
            case Allegiance.Enemy:
                if agent.living_agent.has_boss_glow:
                    if alive:
                        DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.boss, compass.markers.color.profession[agent.living_agent.profession.ToInt()], is_target)
                    else:
                        DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.boss, compass.markers.color.enemy_dead, is_target)
                else:
                    if alive:
                        DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.enemy, is_target)
                    else:
                        DrawAgent(x, y, rot, compass.markers.shape.default, compass.markers.size.default, compass.markers.color.enemy_dead, is_target)
            case _:
                if agent.is_gadget:
                    DrawAgent(x, y, rot, compass.markers.shape.signpost, compass.markers.size.signpost, compass.markers.color.signpost, is_target)
                if agent.is_item:
                    DrawAgent(x, y, rot, compass.markers.shape.item, compass.markers.size.item, compass.markers.color.item, is_target)

def DrawPathing():
    x_offset, y_offset, zoom = Map.MiniMap.MapProjection.ComputedPathingGeometryToScreen(compass.geometry, compass.map_bounds,
                                                                                         *compass.position.player_pos,
                                                                                         compass.position.current_pos.x, compass.position.current_pos.y,
                                                                                         compass.position.current_size, compass.position.rotation)
    
    compass.renderer.set_primitives(compass.geometry, compass.pathing.color)
    compass.renderer.world_space.set_zoom(zoom)
    compass.renderer.world_space.set_rotation(-compass.position.rotation)
    compass.renderer.world_space.set_pan(compass.position.current_pos.x + x_offset,
                                         compass.position.current_pos.y - y_offset)

    compass.renderer.mask.set_circular_mask(True)
    compass.renderer.mask.set_mask_radius(compass.position.current_size*compass.position.culling/Range.Compass.value)
    compass.renderer.mask.set_mask_center(compass.position.current_pos.x, compass.position.current_pos.y)
    compass.renderer.render()

def DrawCompass():
    global compass

    UpdateOrientation()

    if compass.pathing.show:
        DrawPathing()
 
    buffer = compass.position.buffer
    size = compass.position.current_size 
    x = compass.position.current_pos.x - size - buffer
    y = compass.position.current_pos.y - size - buffer
    
    PyImGui.set_next_window_pos(x, y)
    PyImGui.set_next_window_size((size + buffer)*2, (size + buffer)*2)

    if PyImGui.begin("Py4GW Minimap",  PyImGui.WindowFlags.NoTitleBar        |
                                        PyImGui.WindowFlags.NoResize          |
                                        PyImGui.WindowFlags.NoMove            |
                                        PyImGui.WindowFlags.NoScrollbar       |
                                        PyImGui.WindowFlags.NoScrollWithMouse |
                                        PyImGui.WindowFlags.NoCollapse        |
                                        PyImGui.WindowFlags.NoBackground      |
                                        PyImGui.WindowFlags.NoSavedSettings):

        DrawRangeRings()
        DrawAgents()

    PyImGui.end()
        
def configure():
    global compass

    if compass.window_module.first_run:
        PyImGui.set_next_window_pos(compass.window_pos[0], compass.window_pos[1])
        compass.window_module.first_run = False

    end_pos = compass.window_pos
    try:
        if PyImGui.begin(compass.window_module.window_name, compass.window_module.window_flags):
            end_pos = PyImGui.get_window_pos()

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
                compass.position.culling = PyImGui.slider_int('Culling Range',  compass.position.culling,  4000, 5000)

                if not compass.position.snap_to_game:
                    compass.position.always_point_north = PyImGui.checkbox('Always Point North', compass.position.always_point_north)

                    if PyImGui.button('Snap to Screen Center'):
                        display_size = PyOverlay.Overlay().GetDisplaySize()
                        compass.position.detached_pos = PyOverlay.Point2D(round(display_size.x/2),round(display_size.y/2))

                    x = PyImGui.slider_int('X Position', compass.position.detached_pos.x, compass.position.current_size, round(compass.position.display_size.x - compass.position.current_size))
                    y = PyImGui.slider_int('Y Position', compass.position.detached_pos.y, compass.position.current_size, round(compass.position.display_size.y - compass.position.current_size))
                    compass.position.detached_pos  = PyOverlay.Point2D(x,y)
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

            if PyImGui.collapsing_header(f'Pathing'):
                compass.pathing.show = PyImGui.checkbox('Visible', compass.pathing.show)
                compass.pathing.color = Utils.TupleToColor(PyImGui.color_edit4('', Utils.ColorToTuple(compass.pathing.color)))

            PyImGui.pop_style_color(11)

            compass.SaveConfig()
        PyImGui.end()

        compass.ini.write_key('Compass+', 'config_x', str(int(end_pos[0])))
        compass.ini.write_key('Compass+', 'config_y', str(int(end_pos[1])))

    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name # type: ignore
        Py4GW.Console.Log('BOT', f'Error in {current_function}: {str(e)}', Py4GW.Console.MessageType.Error)
        raise

def main():
    global compass, action_queue
    try:
        if not compass.initialized:
            compass.LoadConfig()

        if Map.IsMapLoading():
            compass.reset = True

        if Map.IsMapReady() and Party.IsPartyLoaded() and not UIManager.IsWorldMapShowing():
            if action_queue.IsEmpty('ACTION'):
                action_queue.AddAction('ACTION',UpdateTarget)
            else:
                action_queue.ProcessQueue('ACTION')

            if compass.reset:
                compass.Reset()

            DrawCompass()
            CheckCompassClick()

    except ImportError as e:
        Py4GW.Console.Log('Compass+', f'ImportError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass+', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log('Compass+', f'ValueError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass+', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log('Compass+', f'TypeError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass+', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log('Compass+', f'Unexpected error encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass+', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == '__main__':
    main()