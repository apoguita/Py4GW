


from Bots.oasix.areas.simple_bot_4_steps import SimpleBot4Steps


class StoneCarving(SimpleBot4Steps):
        
    def __init__(self):
        super().__init__()

    @property
    def item_model_id(self) -> int:
        return 820

    @property
    def outpost_id(self) -> int:
        return 287
    
    @property
    def leave_outpost_coords(self) -> list[tuple[float, float]]:
        return [
        (32429, 10764),
    ]

    @property
    def explorable_area_id(self) -> int:
        return 205

    @property
    def explorable_area_coords(self) -> list[tuple[float, float]]:
        return [
            (8821, -8397),
            (8168, -7976),
            (7138, -7421),
            (6390, -6956),
            (5635, -6031),
            (4847, -5703),
            (3873, -5380),
            (3181, -5197),
            (2244, -5468),
            (1179, -5982),
            (667, -6717),
            (-103, -7270),
            (-610, -7269),
            (-1202, -7043),
            (-2055, -6725),
            (-2799, -6560),
            (-3243, -6770),
            (-3369, -7261),
            (-3508, -8126),
            (-4010, -8317),
            (-4876, -8507),
            (-5757, -8090),
            (-6346, -7843),
            (-7574, -7130),
            (-8699, -6450),
            (-8944, -6644),
            (-10098, -5648),
            (-10198, -5748),
            (-9638, -5302),
            (-9071, -5982),
            (-7842, -6754),
            (-10098, -5648),
    ]