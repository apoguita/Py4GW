from Py4GWCoreLib import *

class Marker:
    def __init__(self, name, visible, size, shape, color, fill_range = None, fill_color = None, config = True, custom = False):
        self.name = name
        self.visible = visible
        self.size = size
        self.shape = shape
        self.color = color
        self.fill_range = fill_range
        self.fill_color = fill_color
        self.config = config
        self.custom = custom

    def values(self):
        return (self.visible, self.size, self.shape, self.color, self.fill_range, self.fill_color)

class Ring:
    def __init__(self, name, visible, range, fill_color, outline_color, outline_thickness, custom = False):
        self.name = name
        self.visible = visible
        self.range = range
        self.fill_color = fill_color
        self.outline_color = outline_color
        self.outline_thickness = outline_thickness
        self.custom = custom

class Compass():
    window_module = ImGui.WindowModule('Compass+',window_name='Compass+', window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
    window_pos = (1200,400)
    ini = IniHandler(os.path.join(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")), "Widgets/Config/Compass +.ini"))
    initialized = False
    ini_timer = Timer()

    imgui = PyImGui
    overlay = PyOverlay.Overlay()
    renderer = DXOverlay()

    reset      = True
    frame_id   = 0
    player_id  = 0
    target_id  = 0
    geometry   = []
    primitives_set = False
    map_bounds = []
    frames_to_skip = 1
    frames_skipped = 0
    agent_cache = []
    agent_array = RawAgentArray()

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

    class Pathing:
        visible = True
        color = Utils.RGBToColor(255, 255, 255, 80)

    class Config:
        def __init__(self):
            self.range_rings = []
            self.markers     = {}
            self.profession  = [Utils.RGBToColor(102, 102, 102, 255),
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

            self.death_alpha_mod = .33
            self.spirit_range_alpha = 50

            self.eoe          = Utils.RGBToColor(  0, 255,   0,  50)
            self.qz           = Utils.RGBToColor(  0,   0, 255,  50)
            self.winnowing    = Utils.RGBToColor(  0, 255 ,255,  50)

            # range rings
            self.AddRangeRing('Touch',      False, Range.Touch.value,     Utils.RGBToColor(255, 255 , 255,   0), Utils.RGBToColor(255, 255 , 255, 255), 1.5)
            self.AddRangeRing('Adjacent',   False, Range.Adjacent.value,  Utils.RGBToColor(255, 255 , 255,   0), Utils.RGBToColor(255, 255 , 255, 255), 1.5)
            self.AddRangeRing('Nearby',     False, Range.Nearby.value,    Utils.RGBToColor(255, 255 , 255,   0), Utils.RGBToColor(255, 255 , 255, 255), 1.5)
            self.AddRangeRing('Area',       False, Range.Area.value,      Utils.RGBToColor(255, 255 , 255,   0), Utils.RGBToColor(255, 255 , 255, 255), 1.5)
            self.AddRangeRing('Earshot',    True,  Range.Earshot.value,   Utils.RGBToColor(255, 255 , 255,   0), Utils.RGBToColor(255, 255 , 255, 255), 1.5)
            self.AddRangeRing('Spellcast',  True,  Range.Spellcast.value, Utils.RGBToColor(255, 255 , 255,   0), Utils.RGBToColor(255, 255 , 255, 255), 1.5)
            self.AddRangeRing('Spirit',     True,  Range.Spirit.value,    Utils.RGBToColor(255, 255 , 255,   0), Utils.RGBToColor(255, 255 , 255, 255), 1.5)
            self.AddRangeRing('Compass',    False, Range.Compass.value,   Utils.RGBToColor(255, 255 , 255,   0), Utils.RGBToColor(255, 255 , 255, 255), 1.5)

            # markers
            self.AddMarker('Player',             True, 6, 'Tear',   Utils.RGBToColor(255, 128,   0, 255))
            self.AddMarker('Players',            True, 6, 'Tear',   Utils.RGBToColor(100, 100, 255, 255))
            self.AddMarker('Ally',               True, 6, 'Tear',   Utils.RGBToColor(  0, 179,   0, 255))
            self.AddMarker('Ally (NPC)',         True, 6, 'Tear',   Utils.RGBToColor(153, 255, 153, 255))
            self.AddMarker('Ally (Pet)',         True, 6, 'Tear',   Utils.RGBToColor(125, 255,   0, 255))
            self.AddMarker('Ally (Minion)',      True, 3, 'Tear',   Utils.RGBToColor(  0, 128,  96, 255))
            self.AddMarker('Minipet',            True, 3, 'Tear',   Utils.RGBToColor(153, 255, 153, 255))
            self.AddMarker('Neutral',            True, 6, 'Tear',   Utils.RGBToColor(  0,   0, 220, 255))
            self.AddMarker('Enemy',              True, 6, 'Tear',   Utils.RGBToColor(240,   0,   0, 255))
            self.AddMarker('Spirit (Ranger)',    True, 6, 'Circle', Utils.RGBToColor(204, 255, 153, 255))
            self.AddMarker('Spirit (Ritualist)', True, 6, 'Tear',   Utils.RGBToColor(187, 255, 255, 255))
            self.AddMarker('Spirit (Vanguard)',  True, 6, 'Circle', Utils.RGBToColor( 66,   3,   1, 255))
            self.AddMarker('Item (White)',       True, 5, 'Circle', Utils.RGBToColor(255, 255, 255, 255))
            self.AddMarker('Item (Blue)',        True, 5, 'Circle', Utils.RGBToColor(  0, 170, 255, 255))
            self.AddMarker('Item (Purple)',      True, 5, 'Circle', Utils.RGBToColor(110,  65, 200, 255))
            self.AddMarker('Item (Gold)',        True, 5, 'Circle', Utils.RGBToColor(225, 150,   0, 255))
            self.AddMarker('Item (Green)',       True, 5, 'Circle', Utils.RGBToColor( 25, 200,   0, 255))
            self.AddMarker('Signpost',           True, 5, 'Circle', Utils.RGBToColor(120, 120, 120, 255))

            # spirits
            self.AddMarker(SpiritModelID.BRAMBLES,              True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.CONFLAGRATION,         True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.EDGE_OF_EXTINCTION,    True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.ENERGIZING_WIND,       True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.EQUINOX,               True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.FAMINE,                True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.FAVORABLE_WINDS,       True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.FERTILE_SEASON,        True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.FROZEN_SOIL,           True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.GREATER_CONFLAGRATION, True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.INFURIATING_HEAT,      True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.LACERATE,              True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.MUDDY_TERRAIN,         True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.NATURES_RENEWAL,       True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.PESTILENCE,            True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.PREDATORY_SEASON,      True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.PRIMAL_ECHOES,         True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.QUICKENING_ZEPHYR,     True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.QUICKSAND,             True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.ROARING_WINDS,         True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.SYMBIOSIS,             True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.TOXICITY,              True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.TRANQUILITY,           True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.WINNOWING,             True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.WINTER,                True, 5, 'Circle', Utils.RGBToColor(204, 255, 153, 255),  Range.Spirit.value, Utils.RGBToColor(204, 255, 153, self.spirit_range_alpha), False)

            self.AddMarker(SpiritModelID.DISPLACEMENT,          True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.EARTHBIND,             True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.EMPOWERMENT,           True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.LIFE,                  True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.RECOVERY,              True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.RECUPERATION,          True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)    
            self.AddMarker(SpiritModelID.SHELTER,               True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.SOOTHING,              True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.UNION,                 True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),  Range.Spirit.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.ANGUISH,               True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.BLOODSONG,             True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.DISENCHANTMENT,        True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.DISSONANCE,            True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.PAIN,                  True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.SHADOWSONG,            True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.ANGER,                 True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.HATE,                  True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.SUFFERING,             True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.VAMPIRISM,             True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.WANDERLUST,            True, 5, 'Tear',   Utils.RGBToColor(187, 255, 255, 255),                1350, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.AGONY,                 True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255), Range.Earshot.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.REJUVENATION,          True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255), Range.Earshot.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.PRESERVATION,          True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),    Range.Area.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.DESTRUCTION,           True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),    Range.Area.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)
            self.AddMarker(SpiritModelID.RESTORATION,           True, 5, 'Circle', Utils.RGBToColor(187, 255, 255, 255),    Range.Area.value, Utils.RGBToColor(187, 255, 255, self.spirit_range_alpha), False)

            self.AddMarker(SpiritModelID.WINDS,                 True, 5, 'Circle', Utils.RGBToColor( 66,   3,   1, 255),  Range.Spirit.value, Utils.RGBToColor( 66,   3,   1, self.spirit_range_alpha), False)

        def AddRangeRing(self, name, visible, range, fill_color, outline_color, outline_thickness):
            self.range_rings.append(Ring(name, visible, range, fill_color, outline_color, outline_thickness, custom = True))

        def DeleteRangeRing(self, name):
            for ring in self.range_rings:
                if ring.name == name:
                    self.range_rings.remove(ring)
                    break

        def AddMarker(self, name, visible, size, shape, color, fill_range = None, fill_color = None, config = True, custom = False):
            self.markers[name] = Marker(name, visible, size, shape, color, fill_range, fill_color, config, custom)
        def DeleteMarker(self, name):
            self.markers.pop(name)

    def Reset(self):
        self.reset      = False
        self.frame_id   = Map.MiniMap.GetFrameID()
        self.player_id  = Player.GetAgentID()
        self.geometry   = Map.Pathing.GetComputedGeometry()
        self.primitives_set = False
        self.map_bounds = list(Map.GetMapBoundaries())

    def LoadConfig(self):
        self.initialized = True

        self.window_pos = (self.ini.read_int('position',  'config_x', self.window_pos[0]),
                           self.ini.read_int('position',  'config_y', self.window_pos[1]))

        self.position.snap_to_game       = self.ini.read_bool('position', 'snap_to_game',       self.position.snap_to_game)
        self.position.always_point_north = self.ini.read_bool('position', 'always_point_north', self.position.always_point_north)
        self.position.culling            = self.ini.read_int('position',  'culling',            self.position.culling)
        self.position.detached_pos = PyOverlay.Point2D(
                                           self.ini.read_int('position',  'detached_x',         self.position.detached_pos.x),
                                           self.ini.read_int('position',  'detached_y',         self.position.detached_pos.y))
        self.position.detached_size      = self.ini.read_int('position',  'detached_size',      self.position.detached_size)

        self.pathing.visible  = self.ini.read_bool('pathing', 'visible', self.pathing.visible)
        self.pathing.color = self.ini.read_int( 'pathing', 'color',   self.pathing.color)

        for ring in self.config.range_rings:
            ring.visible           = self.ini.read_bool( f'ring_{ring.name}', 'visible',           ring.visible)
            ring.range             = self.ini.read_int(  f'ring_{ring.name}', 'range',             ring.range)
            ring.fill_color        = self.ini.read_int(  f'ring_{ring.name}', 'fill_color',        ring.fill_color)
            ring.outline_color     = self.ini.read_int(  f'ring_{ring.name}', 'outline_color',     ring.outline_color)
            ring.outline_thickness = self.ini.read_float(f'ring_{ring.name}', 'outline_thickness', ring.outline_thickness)

        for marker in self.config.markers.values():
            marker.visible    = self.ini.read_bool(f'marker_{marker.name}', 'visible',    marker.visible)
            marker.size       = self.ini.read_int( f'marker_{marker.name}', 'size',       marker.size)
            marker.shape      = self.ini.read_key( f'marker_{marker.name}', 'shape',      marker.shape)
            marker.color      = self.ini.read_int( f'marker_{marker.name}', 'color',      marker.color)
            marker.fill_range = self.ini.read_int( f'marker_{marker.name}', 'fill_range', marker.fill_range)
            marker.fill_color = self.ini.read_int( f'marker_{marker.name}', 'fill_color', marker.fill_color)

    def SaveConfig(self):
        if not self.ini_timer.IsRunning():
            self.ini_timer.Start()

        if not self.ini_timer.HasElapsed(1000): return
        self.ini_timer.Reset()

        self.ini.write_key('position', 'snap_to_game',        str(self.position.snap_to_game))
        self.ini.write_key('position', 'always_point_north',  str(self.position.always_point_north))
        self.ini.write_key('position', 'culling',             str(self.position.culling))
        self.ini.write_key('position', 'detached_x',          str(self.position.detached_pos.x))
        self.ini.write_key('position', 'detached_y',          str(self.position.detached_pos.y))
        self.ini.write_key('position', 'detached_size',       str(self.position.detached_size))

        self.ini.write_key('pathing', 'visible', str(self.pathing.visible))
        self.ini.write_key('pathing', 'color',   str(self.pathing.color))

        for ring in self.config.range_rings:
            self.ini.write_key(f'ring_{ring.name}', 'visible',           str(ring.visible))
            self.ini.write_key(f'ring_{ring.name}', 'range',             str(ring.range))
            self.ini.write_key(f'ring_{ring.name}', 'fill_color',        str(ring.fill_color))
            self.ini.write_key(f'ring_{ring.name}', 'outline_color',     str(ring.outline_color))
            self.ini.write_key(f'ring_{ring.name}', 'outline_thickness', str(ring.outline_thickness))

        for marker in self.config.markers.values():
            self.ini.write_key(f'marker_{marker.name}', 'visible',    str(marker.visible))
            self.ini.write_key(f'marker_{marker.name}', 'size',       str(marker.size))
            self.ini.write_key(f'marker_{marker.name}', 'shape',      str(marker.shape))
            self.ini.write_key(f'marker_{marker.name}', 'color',      str(marker.color))
            self.ini.write_key(f'marker_{marker.name}', 'fill_range', str(marker.fill_range))
            self.ini.write_key(f'marker_{marker.name}', 'fill_color', str(marker.fill_color))

    position = Position()
    pathing  = Pathing()
    config   = Config()

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

    for ring in compass.config.range_rings:
        if ring.visible:
            compass.imgui.draw_list_add_circle(compass.position.current_pos.x,
                                               compass.position.current_pos.y,
                                               compass.position.current_size*ring.range/Range.Compass.value,
                                               ring.outline_color,
                                               64,
                                               ring.outline_thickness)
            
            compass.imgui.draw_list_add_circle_filled(compass.position.current_pos.x,
                                                      compass.position.current_pos.y,
                                                      compass.position.current_size*ring.range/Range.Compass.value,
                                                      ring.fill_color,
                                                      64)

def DrawAgent(visible, size, shape, color, fill_range, fill_color, x, y, rotation, is_alive, is_target):
    global compass

    if not visible: return

    if not is_alive:
        col = list(Utils.ColorToTuple(color))
        color = Color(int(col[0]*255), int(col[1]*255), int(col[2]*255), 100).to_color()

    x, y = Map.MiniMap.MapProjection.GamePosToScreen(x, y, *compass.position.player_pos,
                                                            compass.position.current_pos.x, compass.position.current_pos.y,
                                                            compass.position.current_size, compass.position.rotation)

    line_col = Utils.RGBToColor(255,255,0,255) if is_target else Utils.RGBToColor(0,0,0,255)
    line_thickness = 3 if is_target else 1.5

    if fill_range and fill_color:
        compass.imgui.draw_list_add_circle_filled(x, y, compass.position.current_size*fill_range/Range.Compass.value, fill_color, 32)

    if shape == 'Circle':
        compass.imgui.draw_list_add_circle_filled(x, y, size, color, 12)
        compass.imgui.draw_list_add_circle(x, y, size, line_col, 12, line_thickness)
    elif shape == 'Star':
        scale = 1.6

        x1 = math.cos(math.radians( 30))*scale*size + x
        y1 = math.sin(math.radians( 30))*scale*size + y
        x2 = math.cos(math.radians(150))*scale*size + x
        y2 = math.sin(math.radians(150))*scale*size + y
        x3 = math.cos(math.radians(270))*scale*size + x
        y3 = math.sin(math.radians(270))*scale*size + y

        x4 = math.cos(math.radians( 90))*scale*size + x
        y4 = math.sin(math.radians( 90))*scale*size + y
        x5 = math.cos(math.radians(210))*scale*size + x
        y5 = math.sin(math.radians(210))*scale*size + y
        x6 = math.cos(math.radians(330))*scale*size + x
        y6 = math.sin(math.radians(330))*scale*size + y

        a1 = math.cos(math.radians( 60))*scale/1.85*size + x
        b1 = math.sin(math.radians( 60))*scale/1.85*size + y
        a2 = math.cos(math.radians(180))*scale/1.85*size + x
        b2 = math.sin(math.radians(180))*scale/1.85*size + y
        a3 = math.cos(math.radians(300))*scale/1.85*size + x
        b3 = math.sin(math.radians(300))*scale/1.85*size + y

        a4 = math.cos(math.radians(120))*scale/1.85*size + x
        b4 = math.sin(math.radians(120))*scale/1.85*size + y
        a5 = math.cos(math.radians(240))*scale/1.85*size + x
        b5 = math.sin(math.radians(240))*scale/1.85*size + y
        a6 = math.cos(math.radians(  0))*scale/1.85*size + x
        b6 = math.sin(math.radians(  0))*scale/1.85*size + y

        compass.imgui.draw_list_add_triangle_filled(x1, y1, x2, y2, x3, y3, color)
        compass.imgui.draw_list_add_triangle_filled(x4, y4, x5, y5, x6, y6, color)

        compass.imgui.draw_list_add_line(x1, y1, a1, b1, line_col, line_thickness)
        compass.imgui.draw_list_add_line(a1, b1, x4, y4, line_col, line_thickness)
        compass.imgui.draw_list_add_line(x4, y4, a4, b4, line_col, line_thickness)
        compass.imgui.draw_list_add_line(a4, b4, x2, y2, line_col, line_thickness)
        compass.imgui.draw_list_add_line(x2, y2, a2, b2, line_col, line_thickness)
        compass.imgui.draw_list_add_line(a2, b2, x5, y5, line_col, line_thickness)
        compass.imgui.draw_list_add_line(x5, y5, a5, b5, line_col, line_thickness)
        compass.imgui.draw_list_add_line(a5, b5, x3, y3, line_col, line_thickness)
        compass.imgui.draw_list_add_line(x3, y3, a3, b3, line_col, line_thickness)
        compass.imgui.draw_list_add_line(a3, b3, x6, y6, line_col, line_thickness)
        compass.imgui.draw_list_add_line(x6, y6, a6, b6, line_col, line_thickness)
        compass.imgui.draw_list_add_line(a6, b6, x1, y1, line_col, line_thickness)
    else:
        scale = [1,1,1,1]
        if shape == 'Tear':
            scale = [2,1,1,1]
        elif shape == 'Square':
            scale = [1,1,1,1]
        
        x1 = math.cos(rotation                    )*scale[0]*size + x
        y1 = math.sin(rotation                    )*scale[0]*size + y
        x2 = math.cos(rotation + math.radians( 90))*scale[1]*size + x
        y2 = math.sin(rotation + math.radians( 90))*scale[1]*size + y
        x3 = math.cos(rotation + math.radians(180))*scale[2]*size + x
        y3 = math.sin(rotation + math.radians(180))*scale[2]*size + y
        x4 = math.cos(rotation + math.radians(270))*scale[3]*size + x
        y4 = math.sin(rotation + math.radians(270))*scale[3]*size + y

        compass.imgui.draw_list_add_quad_filled(x1, y1, x2, y2, x3, y3, x4, y4, color)
        compass.imgui.draw_list_add_quad(x1, y1, x2, y2, x3, y3, x4, y4, line_col, line_thickness)

def DrawAgents():
    global compass

    def GetAgentValid(agent):
        if agent.id and Utils.Distance((agent.x, agent.y), compass.position.player_pos) <= compass.position.culling:
            return True
        return False
    
    def GetAgentParams(agent):
        return compass.position.rotation - agent.rotation_angle, agent.id == compass.target_id, agent.living_agent.is_alive

    if compass.agent_array.update_throttle.IsExpired():
        compass.agent_cache.clear()
        compass.agent_array.update()
        player_agent = None

        for agent in compass.agent_array.spirit_pet_array:
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            if agent.living_agent.is_spawned:
                if not is_alive:
                    continue
                model_id = agent.living_agent.player_number
                #if model_id in compass.config.spirit_ids['Ranger']:
                compass.agent_cache.append((*compass.config.markers[model_id].values(), agent.x, agent.y, rot, is_alive, is_target))
                #elif model_id in compass.config.spirit_ids['Ritualist']:
                #    compass.agent_cache.append((*compass.config.markers['Spirit (Ritualist)'].values(), x, y, rot, is_alive, is_target))
                #elif model_id in compass.config.spirit_ids['Vanguard']:
                #    compass.agent_cache.append((*compass.config.markers['Spirit (Vanguard)'].values(), x, y, rot, is_alive, is_target))
            else:
                compass.agent_cache.append((*compass.config.markers['Ally (Pet)'].values(), agent.x, agent.y, rot, is_alive, is_target))

        for agent in compass.agent_array.neutral_array:
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            compass.agent_cache.append((*compass.config.markers['Neutral'].values(), agent.x, agent.y, rot, is_alive, is_target))

        for agent in compass.agent_array.minion_array:
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            compass.agent_cache.append((*compass.config.markers['Ally (Minion)'].values(), agent.x, agent.y, rot, is_alive, is_target))

        for agent in compass.agent_array.enemy_array:
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            if agent.living_agent.has_boss_glow:
                compass.agent_cache.append((compass.config.markers['Enemy'].visible, compass.config.markers['Enemy'].size*1.2, compass.config.markers['Enemy'].shape, compass.config.profession[agent.living_agent.profession.ToInt()],
                                            compass.config.markers['Enemy'].fill_range, compass.config.markers['Enemy'].fill_color, agent.x, agent.y, rot, is_alive, is_target))
            else:
                compass.agent_cache.append((*compass.config.markers['Enemy'].values(), agent.x, agent.y, rot, is_alive, is_target))

        for agent in compass.agent_array.ally_array:
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            if agent.living_agent.is_npc:
                compass.agent_cache.append((*compass.config.markers['Ally'].values(), agent.x, agent.y, rot, is_alive, is_target))
            elif agent.id == compass.player_id:
                player_agent = agent
            else:
                compass.agent_cache.append((*compass.config.markers['Players'].values(), agent.x, agent.y, rot, is_alive, is_target))

        for agent in compass.agent_array.npc_minipet_array:
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            if agent.living_agent.has_quest:
                compass.agent_cache.append((compass.config.markers['Ally (NPC)'].visible, compass.config.markers['Ally (NPC)'].size, 'Star', compass.config.markers['Ally (NPC)'].color,
                                            compass.config.markers['Ally (NPC)'].fill_range, compass.config.markers['Ally (NPC)'].fill_color, agent.x, agent.y, rot, is_alive, is_target))
            elif agent.living_agent.level > 1:
                compass.agent_cache.append((*compass.config.markers['Ally (NPC)'].values(), agent.x, agent.y, rot, is_alive, is_target))
            else:
                compass.agent_cache.append((*compass.config.markers['Minipet'].values(), agent.x, agent.y, rot, is_alive, is_target))

        if player_agent and player_agent.id and Utils.Distance((player_agent.x, player_agent.y), compass.position.player_pos) <= compass.position.culling:
            rot, is_target, is_alive = GetAgentParams(player_agent)

            compass.agent_cache.append((*compass.config.markers['Player'].values(), player_agent.x, player_agent.y, rot, is_alive, is_target))

        for agent in compass.agent_array.gadget_array:
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            compass.agent_cache.append((*compass.config.markers['Signpost'].values(), agent.x, agent.y, rot, is_alive, is_target))

        for agent in compass.agent_array.item_array:
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            match Item.item_instance(agent.item_agent.item_id).rarity.value:
                case 1:
                    compass.agent_cache.append((*compass.config.markers['Item (Blue)'].values(), agent.x, agent.y, rot, True, is_target))
                case 2:
                    compass.agent_cache.append((*compass.config.markers['Item (Purple)'].values(), agent.x, agent.y, rot, True, is_target))
                case 3:
                    compass.agent_cache.append((*compass.config.markers['Item (Gold)'].values(), agent.x, agent.y, rot, True, is_target))
                case 4:
                    compass.agent_cache.append((*compass.config.markers['Item (Green)'].values(), agent.x, agent.y, rot, True, is_target))
                case _:
                    compass.agent_cache.append((*compass.config.markers['Item (White)'].values(), agent.x, agent.y, rot, True, is_target))

    [DrawAgent(*cached_agent) for cached_agent in compass.agent_cache]

def DrawPathing():
    x_offset, y_offset, zoom = Map.MiniMap.MapProjection.ComputedPathingGeometryToScreen(compass.map_bounds,
                                                                                         *compass.position.player_pos,
                                                                                         compass.position.current_pos.x, compass.position.current_pos.y,
                                                                                         compass.position.current_size, compass.position.rotation)
    
    if not compass.primitives_set:
        compass.renderer.set_primitives(compass.geometry, compass.pathing.color)
        compass.primitives_set = True

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
 
    buffer = compass.position.buffer
    size = compass.position.current_size 
    x = compass.position.current_pos.x - size - buffer
    y = compass.position.current_pos.y - size - buffer
    
    compass.imgui.set_next_window_pos(x, y)
    compass.imgui.set_next_window_size((size + buffer)*2, (size + buffer)*2)

    if PyImGui.get_io().key_ctrl or PyImGui.get_io().key_alt:
        flags = (PyImGui.WindowFlags.NoTitleBar        | 
                 PyImGui.WindowFlags.NoResize          |
                 PyImGui.WindowFlags.NoMove            |
                 PyImGui.WindowFlags.NoScrollbar       |
                 PyImGui.WindowFlags.NoScrollWithMouse |
                 PyImGui.WindowFlags.NoCollapse        |
                 PyImGui.WindowFlags.NoBackground      |
                 PyImGui.WindowFlags.NoSavedSettings)
    else:
        flags = (PyImGui.WindowFlags.NoTitleBar        |
                 PyImGui.WindowFlags.NoResize          |
                 PyImGui.WindowFlags.NoMove            |
                 PyImGui.WindowFlags.NoScrollbar       |
                 PyImGui.WindowFlags.NoScrollWithMouse |
                 PyImGui.WindowFlags.NoCollapse        |
                 PyImGui.WindowFlags.NoBackground      |
                 PyImGui.WindowFlags.NoMouseInputs     |
                 PyImGui.WindowFlags.NoSavedSettings)

    if compass.imgui.begin("Py4GW Minimap",  flags):

        DrawRangeRings()
        if compass.pathing.visible:
            DrawPathing()
        DrawAgents()

    compass.imgui.end()
        
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
            items = ['Circle','Tear', 'Square']
            if PyImGui.collapsing_header(f'Agents'):
                for marker in compass.config.markers.values():
                    marker.visible = PyImGui.checkbox(f'##Visible{marker.name}', marker.visible)
                    PyImGui.same_line(0.0, -1)
                    PyImGui.push_item_width(80)
                    marker.size = PyImGui.slider_int(f'##Size{marker.name}',  marker.size,  1, 20)
                    PyImGui.pop_item_width()
                    PyImGui.same_line(0.0, -1)
                    PyImGui.push_item_width(80)
                    marker.shape = items[PyImGui.combo(f'##Shape{marker.name}',  items.index(marker.shape),  items)]
                    PyImGui.pop_item_width()
                    PyImGui.same_line(0.0, -1)
                    marker.color = Utils.TupleToColor(PyImGui.color_edit4(f'{marker.name}##Color', Utils.ColorToTuple(marker.color)))

            # range ring settings
            if PyImGui.collapsing_header(f'Range Rings'):
                for ring in compass.config.range_rings:
                    ring.visible = PyImGui.checkbox(f'##Visible{ring.name}', ring.visible)
                    PyImGui.same_line(0.0, -1)
                    ring.fill_color = Utils.TupleToColor(PyImGui.color_edit4(f'##Fill Color{ring.name}', Utils.ColorToTuple(ring.fill_color)))
                    PyImGui.same_line(0.0, -1)
                    ring.outline_color = Utils.TupleToColor(PyImGui.color_edit4(f'##Line Color{ring.name}', Utils.ColorToTuple(ring.outline_color)))
                    PyImGui.same_line(0.0, -1)
                    PyImGui.push_item_width(50)
                    ring.outline_thickness = PyImGui.input_float(f'{ring.name}##Line Thickness', ring.outline_thickness)
                    PyImGui.pop_item_width()

            if PyImGui.collapsing_header(f'Pathing'):
                compass.pathing.visible = PyImGui.checkbox('Visible', compass.pathing.visible)
                compass.pathing.color = Utils.TupleToColor(PyImGui.color_edit4('', Utils.ColorToTuple(compass.pathing.color)))

            if PyImGui.collapsing_header(f'Optimization'):
                compass.frames_to_skip = PyImGui.input_int('Skipped Frames',  compass.frames_to_skip)
                if compass.frames_to_skip < 0:
                    compass.frames_to_skip = 0

            PyImGui.pop_style_color(11)

            compass.SaveConfig()
        PyImGui.end()

        compass.ini.write_key('position', 'config_x', str(int(end_pos[0])))
        compass.ini.write_key('position', 'config_y', str(int(end_pos[1])))

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