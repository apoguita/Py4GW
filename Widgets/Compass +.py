from Py4GWCoreLib import *

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

class Marker:
    def __init__(self, name, visible, size, shape, color, fill_range = None, fill_color = None, model_id = None):
        self.name = name
        self.visible = visible
        self.size = size
        self.shape = shape
        self.color = color
        self.fill_range = fill_range
        self.fill_color = fill_color
        self.model_id = model_id

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
    config_loaded = False

    imgui = PyImGui
    overlay = PyOverlay.Overlay()
    renderer = DXOverlay()

    reset      = True
    player_id  = 0
    target_id  = 0
    target_id_timer = ThrottledTimer(100)
    geometry   = []
    primitives_set = False
    map_bounds = []

    class Position:
        frame_id   = 0
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

        def Update(self):
            self.frame_id = Map.MiniMap.GetFrameID()

            if self.snap_to_game and UIManager.FrameExists(self.frame_id) and UIManager.IsWindowVisible(WindowID.WindowID_Compass):
                coords = UIManager.GetFrameCoords(self.frame_id)

                compass_x, compass_y = Map.MiniMap.GetMapScreenCenter(coords)
                compass_x = round(compass_x)
                compass_y = round(compass_y)

                if compass_x > 100000 or compass_y > 100000:
                    return

                self.snapped_pos = PyOverlay.Point2D(compass_x,compass_y)
                self.snapped_size = round(Map.MiniMap.GetScale(coords))

                self.current_pos = self.snapped_pos
                self.current_size = self.snapped_size
            else:
                self.current_pos = self.detached_pos
                self.current_size = self.detached_size

    class Pathing:
        visible = True
        color = Utils.RGBToColor(255, 255, 255, 80)

    class Config:
        def __init__(self):
            self.range_rings = []
            self.markers     = {}
            self.custom_name = 'Custom Agent Name'
            self.custom_markers = {}
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
            
            self.spirits_ranger = [SpiritModelID.BRAMBLES,
                                   SpiritModelID.CONFLAGRATION,
                                   SpiritModelID.EDGE_OF_EXTINCTION,
                                   SpiritModelID.ENERGIZING_WIND,
                                   SpiritModelID.EQUINOX,
                                   SpiritModelID.FAMINE,
                                   SpiritModelID.FAVORABLE_WINDS,
                                   SpiritModelID.FERTILE_SEASON,
                                   SpiritModelID.FROZEN_SOIL,
                                   SpiritModelID.GREATER_CONFLAGRATION,
                                   SpiritModelID.INFURIATING_HEAT,
                                   SpiritModelID.LACERATE,
                                   SpiritModelID.MUDDY_TERRAIN,
                                   SpiritModelID.NATURES_RENEWAL,
                                   SpiritModelID.PESTILENCE,
                                   SpiritModelID.PREDATORY_SEASON,
                                   SpiritModelID.PRIMAL_ECHOES,
                                   SpiritModelID.QUICKENING_ZEPHYR,
                                   SpiritModelID.QUICKSAND,
                                   SpiritModelID.ROARING_WINDS,
                                   SpiritModelID.SYMBIOSIS,             
                                   SpiritModelID.TOXICITY,
                                   SpiritModelID.TRANQUILITY,
                                   SpiritModelID.WINNOWING,
                                   SpiritModelID.WINTER]
            
            self.spirits_ritualist = {'spirit'  : [SpiritModelID.DISPLACEMENT,
                                                   SpiritModelID.EARTHBIND,
                                                   SpiritModelID.EMPOWERMENT, 
                                                   SpiritModelID.LIFE,
                                                   SpiritModelID.RECOVERY,
                                                   SpiritModelID.RECUPERATION,    
                                                   SpiritModelID.SHELTER,
                                                   SpiritModelID.SOOTHING,
                                                   SpiritModelID.UNION],
                                      'longbow' : [SpiritModelID.ANGUISH,
                                                   SpiritModelID.BLOODSONG,
                                                   SpiritModelID.DISENCHANTMENT,
                                                   SpiritModelID.DISSONANCE,
                                                   SpiritModelID.PAIN,
                                                   SpiritModelID.SHADOWSONG,
                                                   SpiritModelID.ANGER,
                                                   SpiritModelID.HATE,
                                                   SpiritModelID.SUFFERING,
                                                   SpiritModelID.VAMPIRISM,
                                                   SpiritModelID.WANDERLUST], # 1350
                                      'earshot' : [SpiritModelID.AGONY,
                                                   SpiritModelID.REJUVENATION],
                                      'area'    : [SpiritModelID.PRESERVATION,
                                                   SpiritModelID.DESTRUCTION,
                                                   SpiritModelID.RESTORATION]}

            self.spirits_vanguard = [SpiritModelID.WINDS]

            self.death_alpha_mod = .33
            self.spirit_alpha = 50
            self.show_spirit_range = False

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
            self.AddMarker('Ally (Pet)',         True, 4, 'Tear',   Utils.RGBToColor(125, 255,   0, 255))
            self.AddMarker('Ally (Minion)',      True, 3, 'Tear',   Utils.RGBToColor(  0, 128,  96, 255))
            self.AddMarker('Minipet',            True, 3, 'Tear',   Utils.RGBToColor(153, 255, 153, 255))
            self.AddMarker('Neutral',            True, 6, 'Tear',   Utils.RGBToColor(  0,   0, 220, 255))
            self.AddMarker('Enemy',              True, 6, 'Tear',   Utils.RGBToColor(240,   0,   0, 255))
            self.AddMarker('Spirit (Ranger)',    True, 4, 'Circle', Utils.RGBToColor(204, 255, 153, 255))
            self.AddMarker('Spirit (Ritualist)', True, 4, 'Tear',   Utils.RGBToColor(187, 255, 255, 255))
            self.AddMarker('Spirit (Vanguard)',  True, 4, 'Circle', Utils.RGBToColor( 66,   3,   1, 255))
            self.AddMarker('Item (White)',       True, 5, 'Circle', Utils.RGBToColor(255, 255, 255, 255))
            self.AddMarker('Item (Blue)',        True, 5, 'Circle', Utils.RGBToColor(  0, 170, 255, 255))
            self.AddMarker('Item (Purple)',      True, 5, 'Circle', Utils.RGBToColor(110,  65, 200, 255))
            self.AddMarker('Item (Gold)',        True, 5, 'Circle', Utils.RGBToColor(225, 150,   0, 255))
            self.AddMarker('Item (Green)',       True, 5, 'Circle', Utils.RGBToColor( 25, 200,   0, 255))
            self.AddMarker('Signpost',           True, 5, 'Circle', Utils.RGBToColor(120, 120, 120, 255))

        def AddRangeRing(self, name, visible, range, fill_color, outline_color, outline_thickness):
            self.range_rings.append(Ring(name, visible, range, fill_color, outline_color, outline_thickness, custom = True))

        def DeleteRangeRing(self, name):
            for ring in self.range_rings:
                if ring.name == name:
                    self.range_rings.remove(ring)
                    break

        def AddMarker(self, name, visible, size, shape, color, fill_range = None, fill_color = None):
            self.markers[name] = Marker(name, visible, size, shape, color, fill_range, fill_color)

        def AddCustomMarker(self, name):
            self.custom_markers[name] = Marker(name, True, 6, 'Tear', Utils.RGBToColor(125, 125, 125, 255), None, None, 0)

        def DeleteMarker(self, name):
            self.markers.pop(name)

    def LoadConfig(self):
        self.window_pos = (self.ini.read_int('position',  'config_x', self.window_pos[0]),
                           self.ini.read_int('position',  'config_y', self.window_pos[1]))

        self.position.snap_to_game       = self.ini.read_bool('position', 'snap_to_game',       self.position.snap_to_game)
        self.position.always_point_north = self.ini.read_bool('position', 'always_point_north', self.position.always_point_north)
        self.position.culling            = self.ini.read_int('position',  'culling',            self.position.culling)
        self.position.detached_pos = PyOverlay.Point2D(
                                           self.ini.read_int('position',  'detached_x',         self.position.detached_pos.x),
                                           self.ini.read_int('position',  'detached_y',         self.position.detached_pos.y))
        self.position.detached_size      = self.ini.read_int('position',  'detached_size',      self.position.detached_size)

        self.pathing.visible = self.ini.read_bool('pathing', 'visible', self.pathing.visible)
        self.pathing.color = self.ini.read_int('pathing', 'color', self.pathing.color)

        self.config.spirit_alpha = self.ini.read_int('misc', 'spirit_alpha', self.config.spirit_alpha)
        self.config.show_spirit_range = self.ini.read_bool('misc', 'show_spirit_ranges', self.config.show_spirit_range)

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

        for section in self.ini.list_sections():
            if str(section).startswith('custom_marker_'):
                name       = str(section).removeprefix('custom_marker_')
                model_id   = self.ini.read_int( section, 'model_id',   0)
                visible    = self.ini.read_bool(section, 'visible',    True)
                size       = self.ini.read_int( section, 'size',       6)
                shape      = self.ini.read_key( section, 'shape',      'Tear')
                color      = self.ini.read_int( section, 'color',      Utils.RGBToColor(125, 125, 125, 255))
                fill_range = self.ini.read_int( section, 'fill_range', 0)
                fill_color = self.ini.read_int( section, 'fill_color', Utils.RGBToColor(125, 125, 125, self.config.spirit_alpha))
                self.config.custom_markers[name] = Marker(name, visible, size, shape, color, fill_range, fill_color, model_id)

    def SaveConfig(self):
        self.ini.write_key('position', 'snap_to_game',        str(self.position.snap_to_game))
        self.ini.write_key('position', 'always_point_north',  str(self.position.always_point_north))
        self.ini.write_key('position', 'culling',             str(self.position.culling))
        self.ini.write_key('position', 'detached_x',          str(self.position.detached_pos.x))
        self.ini.write_key('position', 'detached_y',          str(self.position.detached_pos.y))
        self.ini.write_key('position', 'detached_size',       str(self.position.detached_size))

        self.ini.write_key('pathing', 'visible', str(self.pathing.visible))
        self.ini.write_key('pathing', 'color',   str(self.pathing.color))

        self.ini.write_key('misc', 'spirit_alpha', str(self.config.spirit_alpha))
        self.ini.write_key('misc', 'show_spirit_ranges', str(self.config.show_spirit_range))

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

        for marker in self.config.custom_markers.values():
            self.ini.write_key(f'custom_marker_{marker.name}', 'model_id',   str(marker.model_id))
            self.ini.write_key(f'custom_marker_{marker.name}', 'visible',    str(marker.visible))
            self.ini.write_key(f'custom_marker_{marker.name}', 'size',       str(marker.size))
            self.ini.write_key(f'custom_marker_{marker.name}', 'shape',      str(marker.shape))
            self.ini.write_key(f'custom_marker_{marker.name}', 'color',      str(marker.color))
            self.ini.write_key(f'custom_marker_{marker.name}', 'fill_range', str(marker.fill_range))
            self.ini.write_key(f'custom_marker_{marker.name}', 'fill_color', str(marker.fill_color))

    def UpdateOrientation(self):
        self.position.player_pos = Player.GetXY()

        if self.position.snap_to_game:
            self.position.rotation = Map.MiniMap.GetRotation()
        else:
            if self.position.always_point_north:
                self.position.rotation = 0
            else:
                self.position.rotation = Camera.GetCurrentYaw() - math.pi/2

    def DrawRangeRings(self):
        for ring in self.config.range_rings:
            if ring.visible:
                if not Map.IsMapReady():
                    return
                
                self.imgui.draw_list_add_circle(self.position.current_pos.x,
                                                self.position.current_pos.y,
                                                self.position.current_size*ring.range/Range.Compass.value,
                                                ring.outline_color,
                                                64,
                                                ring.outline_thickness)
                
                self.imgui.draw_list_add_circle_filled(self.position.current_pos.x,
                                                       self.position.current_pos.y,
                                                       self.position.current_size*ring.range/Range.Compass.value,
                                                       ring.fill_color,
                                                       64)

    def DrawPathing(self):
        x_offset, y_offset, zoom = Map.MiniMap.MapProjection.ComputedPathingGeometryToScreen(self.map_bounds,
                                                                                             *self.position.player_pos,
                                                                                             self.position.current_pos.x, self.position.current_pos.y,
                                                                                             self.position.current_size, self.position.rotation)
        
        if not self.primitives_set:
            self.renderer.set_primitives(self.geometry, self.pathing.color)
            self.primitives_set = True

        self.renderer.world_space.set_zoom(zoom)
        self.renderer.world_space.set_rotation(-self.position.rotation)
        self.renderer.world_space.set_pan(self.position.current_pos.x + x_offset,
                                            self.position.current_pos.y - y_offset)

        self.renderer.mask.set_circular_mask(True)
        self.renderer.mask.set_mask_radius(self.position.current_size*self.position.culling/Range.Compass.value)
        self.renderer.mask.set_mask_center(self.position.current_pos.x, self.position.current_pos.y)

        if not Map.IsMapReady():
            return

        self.renderer.render()

    def DrawAgent(self, visible, size, shape, color, fill_range, fill_color, x, y, rotation, is_alive, is_target):
        if not Map.IsMapReady() or not visible: return

        if not is_alive:
            col = Utils.ColorToTuple(color)
            color = Color(int(col[0]*255), int(col[1]*255), int(col[2]*255), 100).to_color()

        x, y = Map.MiniMap.MapProjection.GamePosToScreen(x, y, *self.position.player_pos,
                                                                self.position.current_pos.x, self.position.current_pos.y,
                                                                self.position.current_size, self.position.rotation)

        line_col = Utils.RGBToColor(255,255,0,255) if is_target else Utils.RGBToColor(0,0,0,255)
        line_thickness = 3 if is_target else 1.5

        if fill_range and fill_color:
            self.imgui.draw_list_add_circle_filled(x, y, self.position.current_size*fill_range/Range.Compass.value, fill_color, 32)

        if shape == 'Circle':
            self.imgui.draw_list_add_circle_filled(x, y, size, color, 12)
            self.imgui.draw_list_add_circle(x, y, size, line_col, 12, line_thickness)
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

            self.imgui.draw_list_add_triangle_filled(x1, y1, x2, y2, x3, y3, color)
            self.imgui.draw_list_add_triangle_filled(x4, y4, x5, y5, x6, y6, color)

            self.imgui.draw_list_add_line(x1, y1, a1, b1, line_col, line_thickness)
            self.imgui.draw_list_add_line(a1, b1, x4, y4, line_col, line_thickness)
            self.imgui.draw_list_add_line(x4, y4, a4, b4, line_col, line_thickness)
            self.imgui.draw_list_add_line(a4, b4, x2, y2, line_col, line_thickness)
            self.imgui.draw_list_add_line(x2, y2, a2, b2, line_col, line_thickness)
            self.imgui.draw_list_add_line(a2, b2, x5, y5, line_col, line_thickness)
            self.imgui.draw_list_add_line(x5, y5, a5, b5, line_col, line_thickness)
            self.imgui.draw_list_add_line(a5, b5, x3, y3, line_col, line_thickness)
            self.imgui.draw_list_add_line(x3, y3, a3, b3, line_col, line_thickness)
            self.imgui.draw_list_add_line(a3, b3, x6, y6, line_col, line_thickness)
            self.imgui.draw_list_add_line(x6, y6, a6, b6, line_col, line_thickness)
            self.imgui.draw_list_add_line(a6, b6, x1, y1, line_col, line_thickness)
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

            self.imgui.draw_list_add_quad_filled(x1, y1, x2, y2, x3, y3, x4, y4, color)
            self.imgui.draw_list_add_quad(x1, y1, x2, y2, x3, y3, x4, y4, line_col, line_thickness)

    def DrawAgents(self):
        def GetAgentValid(agent):
            if agent.id and Utils.Distance((agent.x, agent.y), self.position.player_pos) <= self.position.culling:
                return True
            return False
        
        def GetAgentParams(agent):
            return self.position.rotation - agent.rotation_angle, agent.id == self.target_id, agent.living_agent.is_alive
        
        def CheckCustomMarkers(agent):
            model_id = agent.living_agent.player_number
            for marker in self.config.custom_markers.values():
                if marker.visible and model_id == marker.model_id:
                    rot, is_target, is_alive = GetAgentParams(agent)
                    if marker.fill_range > 0:
                        color = Utils.ColorToTuple(marker.color)
                        fill_color = Utils.TupleToColor((color[0],color[1],color[2],self.config.spirit_alpha/255))
                    else:
                        fill_color = None
                    self.DrawAgent(marker.visible, marker.size, marker.shape, marker.color, marker.fill_range, fill_color, agent.x, agent.y, rot, is_alive, is_target) # type: ignore
                    return True
            return False

        agent_array = GLOBAL_CACHE.AgentArray
        player_agent = None
        self.player_id = GLOBAL_CACHE.Player.GetAgentID()
        self.target_id = GLOBAL_CACHE.Player.GetTargetID()

        for agent in agent_array.GetRawSpiritPetArray():
            if not GetAgentValid(agent): continue
            if CheckCustomMarkers(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            if agent.living_agent.is_spawned:
                if not is_alive:
                    continue
                model_id = agent.living_agent.player_number
                if model_id in self.config.spirits_ranger:
                    if self.config.show_spirit_range:
                        color = Utils.ColorToTuple(self.config.markers['Spirit (Ranger)'].color)
                        fill_color = Utils.TupleToColor((color[0],color[1],color[2],self.config.spirit_alpha/255))
                    else:
                        fill_color = None
                    self.DrawAgent(self.config.markers['Spirit (Ranger)'].visible, self.config.markers['Spirit (Ranger)'].size, 
                                   self.config.markers['Spirit (Ranger)'].shape, self.config.markers['Spirit (Ranger)'].color, 
                                   Range.Spirit.value, fill_color, 
                                   agent.x, agent.y, rot, is_alive, is_target)
                elif model_id in self.config.spirits_ritualist['spirit']:
                    if self.config.show_spirit_range:
                        color = Utils.ColorToTuple(self.config.markers['Spirit (Ritualist)'].color)
                        fill_color = Utils.TupleToColor((color[0],color[1],color[2],self.config.spirit_alpha/255))
                    else:
                        fill_color = None
                    self.DrawAgent(self.config.markers['Spirit (Ritualist)'].visible, self.config.markers['Spirit (Ritualist)'].size, 
                                   'Circle', self.config.markers['Spirit (Ritualist)'].color, 
                                   Range.Spirit.value, fill_color, 
                                   agent.x, agent.y, rot, is_alive, is_target)
                elif model_id in self.config.spirits_ritualist['longbow']:
                    if self.config.show_spirit_range:
                        color = Utils.ColorToTuple(self.config.markers['Spirit (Ritualist)'].color)
                        fill_color = Utils.TupleToColor((color[0],color[1],color[2],self.config.spirit_alpha/255))
                    else:
                        fill_color = None
                    self.DrawAgent(self.config.markers['Spirit (Ritualist)'].visible, self.config.markers['Spirit (Ritualist)'].size, 
                                   self.config.markers['Spirit (Ritualist)'].shape, self.config.markers['Spirit (Ritualist)'].color, 
                                   1350, fill_color, 
                                   agent.x, agent.y, rot, is_alive, is_target)
                elif model_id in self.config.spirits_ritualist['earshot']:
                    if self.config.show_spirit_range:
                        color = Utils.ColorToTuple(self.config.markers['Spirit (Ritualist)'].color)
                        fill_color = Utils.TupleToColor((color[0],color[1],color[2],self.config.spirit_alpha/255))
                    else:
                        fill_color = None
                    self.DrawAgent(self.config.markers['Spirit (Ritualist)'].visible, self.config.markers['Spirit (Ritualist)'].size, 
                                   'Circle', self.config.markers['Spirit (Ritualist)'].color, 
                                   Range.Earshot.value, fill_color, 
                                   agent.x, agent.y, rot, is_alive, is_target)
                elif model_id in self.config.spirits_ritualist['area']:
                    if self.config.show_spirit_range:
                        color = Utils.ColorToTuple(self.config.markers['Spirit (Ritualist)'].color)
                        fill_color = Utils.TupleToColor((color[0],color[1],color[2],self.config.spirit_alpha/255))
                    else:
                        fill_color = None
                    self.DrawAgent(self.config.markers['Spirit (Ritualist)'].visible, self.config.markers['Spirit (Ritualist)'].size, 
                                   'Circle', self.config.markers['Spirit (Ritualist)'].color, 
                                   Range.Area.value, fill_color, 
                                   agent.x, agent.y, rot, is_alive, is_target)
                elif model_id in self.config.spirits_vanguard:
                    if self.config.show_spirit_range:
                        color = Utils.ColorToTuple(self.config.markers['Spirit (Vanguard)'].color)
                        fill_color = Utils.TupleToColor((color[0],color[1],color[2],self.config.spirit_alpha/255))
                    else:
                        fill_color = None
                    self.DrawAgent(self.config.markers['Spirit (Vanguard)'].visible, self.config.markers['Spirit (Vanguard)'].size, 
                                   self.config.markers['Spirit (Vanguard)'].shape, self.config.markers['Spirit (Vanguard)'].color, 
                                   Range.Spirit.value, fill_color, 
                                   agent.x, agent.y, rot, is_alive, is_target)
            else:
                self.DrawAgent(*self.config.markers['Ally (Pet)'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore

        for agent in agent_array.GetRawNeutralArray():
            if not GetAgentValid(agent): continue
            if CheckCustomMarkers(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            self.DrawAgent(*self.config.markers['Neutral'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore

        for agent in agent_array.GetRawMinionArray():
            if not GetAgentValid(agent): continue
            if CheckCustomMarkers(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            self.DrawAgent(*self.config.markers['Ally (Minion)'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore

        for agent in agent_array.GetRawEnemyArray():
            if not GetAgentValid(agent): continue
            if CheckCustomMarkers(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            if agent.living_agent.has_boss_glow:
                self.DrawAgent(self.config.markers['Enemy'].visible, self.config.markers['Enemy'].size*1.2, self.config.markers['Enemy'].shape, self.config.profession[agent.living_agent.profession.ToInt()],
                                            self.config.markers['Enemy'].fill_range, self.config.markers['Enemy'].fill_color, agent.x, agent.y, rot, is_alive, is_target)
            else:
                self.DrawAgent(*self.config.markers['Enemy'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore

        for agent in agent_array.GetRawAllyArray():
            if not GetAgentValid(agent): continue
            if CheckCustomMarkers(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            if agent.living_agent.is_npc:
                self.DrawAgent(*self.config.markers['Ally'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore
            elif agent.id == self.player_id:
                player_agent = agent
            else:
                self.DrawAgent(*self.config.markers['Players'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore

        for agent in agent_array.GetRawNPCMinipetArray():
            if not GetAgentValid(agent): continue
            if CheckCustomMarkers(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            if agent.living_agent.has_quest:
                self.DrawAgent(self.config.markers['Ally (NPC)'].visible, self.config.markers['Ally (NPC)'].size, 'Star', self.config.markers['Ally (NPC)'].color,
                                            self.config.markers['Ally (NPC)'].fill_range, self.config.markers['Ally (NPC)'].fill_color, agent.x, agent.y, rot, is_alive, is_target)
            elif agent.living_agent.level > 1:
                self.DrawAgent(*self.config.markers['Ally (NPC)'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore
            else:
                self.DrawAgent(*self.config.markers['Minipet'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore

        if player_agent and player_agent.id and Utils.Distance((player_agent.x, player_agent.y), self.position.player_pos) <= self.position.culling:
            rot, is_target, is_alive = GetAgentParams(player_agent)

            self.DrawAgent(*self.config.markers['Player'].values(), player_agent.x, player_agent.y, rot, is_alive, is_target) # type: ignore

        for agent in agent_array.GetRawGadgetArray():
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            self.DrawAgent(*self.config.markers['Signpost'].values(), agent.x, agent.y, rot, is_alive, is_target) # type: ignore

        for agent in agent_array.GetRawItemArray():
            if not GetAgentValid(agent): continue
            rot, is_target, is_alive = GetAgentParams(agent)

            match Item.item_instance(agent.item_agent.item_id).rarity.value:
                case 1:
                    self.DrawAgent(*self.config.markers['Item (Blue)'].values(), agent.x, agent.y, rot, True, is_target) # type: ignore
                case 2:
                    self.DrawAgent(*self.config.markers['Item (Purple)'].values(), agent.x, agent.y, rot, True, is_target) # type: ignore
                case 3:
                    self.DrawAgent(*self.config.markers['Item (Gold)'].values(), agent.x, agent.y, rot, True, is_target) # type: ignore
                case 4:
                    self.DrawAgent(*self.config.markers['Item (Green)'].values(), agent.x, agent.y, rot, True, is_target) # type: ignore
                case _:
                    self.DrawAgent(*self.config.markers['Item (White)'].values(), agent.x, agent.y, rot, True, is_target) # type: ignore

    def Draw(self):
        self.UpdateOrientation()
    
        buffer = self.position.buffer
        size = self.position.current_size 
        x = self.position.current_pos.x - size - buffer
        y = self.position.current_pos.y - size - buffer
        
        self.imgui.set_next_window_pos(x, y)
        self.imgui.set_next_window_size((size + buffer)*2, (size + buffer)*2)

        if self.imgui.get_io().key_ctrl or self.imgui.get_io().key_alt:
            flags = (self.imgui.WindowFlags.NoTitleBar        | 
                     self.imgui.WindowFlags.NoResize          |
                     self.imgui.WindowFlags.NoMove            |
                     self.imgui.WindowFlags.NoScrollbar       |
                     self.imgui.WindowFlags.NoScrollWithMouse |
                     self.imgui.WindowFlags.NoCollapse        |
                     self.imgui.WindowFlags.NoBackground      |
                     self.imgui.WindowFlags.NoSavedSettings)
        else:
            flags = (self.imgui.WindowFlags.NoTitleBar        |
                     self.imgui.WindowFlags.NoResize          |
                     self.imgui.WindowFlags.NoMove            |
                     self.imgui.WindowFlags.NoScrollbar       |
                     self.imgui.WindowFlags.NoScrollWithMouse |
                     self.imgui.WindowFlags.NoCollapse        |
                     self.imgui.WindowFlags.NoBackground      |
                     self.imgui.WindowFlags.NoMouseInputs     |
                     self.imgui.WindowFlags.NoSavedSettings)

        if self.imgui.begin("Py4GW Minimap",  flags):

            self.DrawRangeRings()
            if self.pathing.visible:
                self.DrawPathing()
            #timer = Timer()
            #timer.Start()
            self.DrawAgents()
            #Debug(timer.GetElapsedTime())

        self.imgui.end()

    def CheckClick(self):
        if self.imgui.is_mouse_clicked(0): 
            if self.imgui.get_io().key_ctrl:
                pos = self.overlay.GetMouseCoords()
                mouse_pos = (pos.x, pos.y)
                world_pos = Map.MiniMap.MapProjection.ScreenToGamePos(*mouse_pos,
                                                                      *self.position.player_pos,
                                                                      self.position.current_pos.x, self.position.current_pos.y,
                                                                      self.position.current_size, 
                                                                      self.position.rotation)

                agent_array = GLOBAL_CACHE.AgentArray.GetAgentArray()
                agent_array = AgentArray.Sort.ByDistance(agent_array, world_pos)
                if len(agent_array) > 0:
                    GLOBAL_CACHE.Player.ChangeTarget(agent_array[0])

            if self.imgui.get_io().key_alt:
                pos = self.overlay.GetMouseCoords()
                mouse_pos = (pos.x, pos.y)

                world_pos = Map.MiniMap.MapProjection.ScreenToGamePos(*mouse_pos,
                                                                      *self.position.player_pos,
                                                                      self.position.current_pos.x, self.position.current_pos.y,
                                                                      self.position.current_size, 
                                                                      self.position.rotation)
                GLOBAL_CACHE.Player.Move(*world_pos)

    def Update(self):
        if not self.config_loaded:
            self.LoadConfig()
            self.config_loaded = True

        if Map.IsMapLoading() or Player.InCharacterSelectScreen():
            self.reset = True
            return

        if Map.IsMapReady() and Party.IsPartyLoaded() and not UIManager.IsWorldMapShowing():
            if self.reset:
                self.reset          = False
                self.geometry       = Map.Pathing.GetComputedGeometry()
                self.primitives_set = False
                self.map_bounds     = list(GLOBAL_CACHE.Map.GetMapBoundaries())
                self.position.Update()

            self.Draw()
            self.CheckClick()

    position = Position()
    pathing  = Pathing()
    config   = Config()

compass = Compass()

def configure():
    global compass

    compass.position.Update()

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

            header_opened = False

            # position settings
            if PyImGui.collapsing_header(f'Position'):
                PyImGui.indent(10)
                header_opened = True
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
                PyImGui.unindent(10)

            # agent settings
            items = ['Circle','Tear', 'Square']
            if PyImGui.collapsing_header(f'Agents'):
                PyImGui.indent(10)

                header_opened = True
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

                PyImGui.separator()

                compass.config.show_spirit_range = PyImGui.checkbox(f'Show Spirit Ranges', compass.config.show_spirit_range)
                compass.config.spirit_alpha = PyImGui.slider_int(f'Spirit Range Alpha', compass.config.spirit_alpha, 0, 255)

                PyImGui.separator()

                PyImGui.indent(4)
                for name, marker in compass.config.custom_markers.items():
                    if PyImGui.collapsing_header(f'{name}##header'):
                        PyImGui.indent(10)
                        marker.model_id = PyImGui.input_int(f'Model ID##{name}', marker.model_id)

                        if PyImGui.button(f'Get Model ID from Target##{name}'):
                            marker.model_id = Agent.GetPlayerNumber(Player.GetTargetID())

                        marker.visible = PyImGui.checkbox(f'Visible##{name}', marker.visible)
                        marker.size = PyImGui.slider_int(f'Size##{name}',  marker.size,  1, 20)
                        items = ['Circle','Tear', 'Square']
                        marker.shape = items[PyImGui.combo(f'Shape##{name}',  items.index(marker.shape),  items)]
                        marker.color = Utils.TupleToColor(PyImGui.color_edit4(f'Color##{name}', Utils.ColorToTuple(marker.color)))
                        marker.fill_range = PyImGui.slider_int(f'Fill Range##{name}',  marker.fill_range or 0,  0, 5000)
                        if PyImGui.button(f'Delete Marker##{name}'):
                            compass.config.custom_markers.pop(name)
                            compass.ini.delete_section(f'custom_marker_{name}')
                            break
                        PyImGui.unindent(10)
                PyImGui.unindent(4)

                if PyImGui.button('Add Custom Agent'):
                    compass.config.AddCustomMarker(compass.config.custom_name)
                    compass.config.custom_name = 'Custom Agent Name'
                PyImGui.same_line(0.0, -1)
                compass.config.custom_name = PyImGui.input_text('##agent_name', compass.config.custom_name)

                PyImGui.unindent(10)

            # range ring settings
            if PyImGui.collapsing_header(f'Range Rings'):
                PyImGui.indent(10)
                header_opened = True
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
                PyImGui.unindent(10)

            if PyImGui.collapsing_header(f'Pathing'):
                PyImGui.indent(10)
                header_opened = True
                compass.pathing.visible = PyImGui.checkbox('Visible', compass.pathing.visible)
                compass.pathing.color = Utils.TupleToColor(PyImGui.color_edit4('', Utils.ColorToTuple(compass.pathing.color)))
                PyImGui.unindent(10)

            if PyImGui.button('Save Settings', PyImGui.get_window_width() - 20 if header_opened else 150):
                compass.SaveConfig()

            PyImGui.pop_style_color(11)
        PyImGui.end()

        compass.ini.write_key('position', 'config_x', str(int(end_pos[0])))
        compass.ini.write_key('position', 'config_y', str(int(end_pos[1])))

    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name # type: ignore
        Py4GW.Console.Log('BOT', f'Error in {current_function}: {str(e)}', Py4GW.Console.MessageType.Error)
        raise

def main():
    global compass
    try:
        compass.Update()

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