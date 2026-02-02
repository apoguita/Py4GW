class Waypoint2D(tuple):
    __slots__ = ()

    def __new__(cls, x: float, y: float):
        return super().__new__(cls, (float(x), float(y)))

    @property
    def x(self) -> float:
        return self[0]

    @property
    def y(self) -> float:
        return self[1]


class Waypoint3D:
    __slots__ = ("_x", "_y", "_z", "_distance")

    def __init__(self, x: float, y: float, z: float):
        self._x = float(x)
        self._y = float(y)
        self._z = float(z)
        self._distance = 0.0

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float):
        self._x = float(value)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float):
        self._y = float(value)

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, value: float):
        self._z = float(value)
        
    @property
    def distance(self) -> float:
        return self._distance
    
    @distance.setter
    def distance(self, value: float):
        self._distance = float(value)
    
    def as_tuple(self) -> tuple[float, float, float]:
        return (self._x, self._y, self._z)
    
    def with_z(self, z: float) -> "Waypoint3D":
        return Waypoint3D(self._x, self._y, float(z))

from typing import Dict


class Waypoints(dict[int, list[Waypoint3D]]):

    def __init__(self):
        super().__init__()

        raw_waypoint_dict: Dict[int, list[tuple[float, float]]] = {
            444: [
                (16081.63, -11048.55),
                (16205.75, -11561.24),
                (16573.59, -12127.98),
                (16796.12, -12380.12),
                (17619.33, -13093.12),
                (17361.46, -13667.42),
                (16346.84, -13510.79),
                (15204.45, -13802.76),
                (13894.67, -14068.41),
                (12257.97, -13667.80),
                (11530.83, -13535.98),
                (10344.16, -13491.97),
                (9160.40, -13136.81),
                (8865.66, -12580.95),
                (8064.00, -12192.00),
                (7345.84, -11481.20),
                (-516.13, -6785.55),
                (-306.18, -6072.92),
                (-509.03, -5390.10),
                (0.62, -4241.59),
                (44.10, -2897.30),
                (175.36, -1626.59),
                (-21.74, -724.51),
                (706.58, -105.54),
                (931.35, 944.19),
                (-4425.78, 7941.06),
                (-4030.56, 10930.51),
                (-4857.11, 8839.57),
                (-4128.81, 9406.73),
                (-4277.01, 10218.22),
                (-3048.67, 11634.17),
                (-1516.45, 11495.00),
                
                (-940.59, 12183.17),
                
            ],
            437: [
                (4465.54, -16118.44),
                (5902.26, -14744.68),
                (6435.12, -13821.38),
                (7723.12, -13543.52),
                (8420.34, -12646.81),
                (9466.96, -11992.94),
                (10401.58, -11021.58),
                (10968.76, -8763.79),
                (11302.09, -7145.48),
            ],
        }

        for map_id, points in raw_waypoint_dict.items():
            self[map_id] = [Waypoint3D(*p, 0.0) for p in points]
