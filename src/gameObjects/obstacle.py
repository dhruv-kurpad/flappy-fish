import math
from pathlib import Path
from gameObjects.game_object import GameObject
from gameObjects.sprite import Sprite

_ASSETS = Path(__file__).resolve().parent.parent / "assets"


class Obstacle(GameObject):
    def __init__(
        self,
        x: float,
        y: float,
        sprite_path,
        amplitude: float = 0.0,
        frequency: float = 0.0,
        min_y: float = 0.0,
        max_y: float = 0.0,
    ):
        # Accept bool (True=top, False=bottom) for backwards compatibility with tests.
        if isinstance(sprite_path, bool):
            name = "tentacles_top.txt" if sprite_path else "tentacles_bottom.txt"
            sprite_path = str(_ASSETS / name)
        self._x_float: float = float(x)
        self._y_float: float = float(y)
        self._base_y: float = float(y)
        self._position = (int(self._x_float), int(round(self._y_float)))
        self._sprite = Sprite(sprite_path)
        self._amplitude: float = amplitude
        self._frequency: float = frequency
        self._time: float = 0.0
        self._min_y: float = float(min_y)
        self._max_y: float = float(max_y)

    def set_x(self, x_float: float) -> None:
        """Called by the spawner each frame to scroll the obstacle left."""
        self._x_float = x_float
        self._position = (int(self._x_float), int(round(self._y_float)))

    def set_base_y(self, y: float) -> None:
        """Spawner calls this on fresh spawn to reset the oscillation center."""
        self._base_y = y
        self._y_float = y
        self._position = (int(self._x_float), int(round(y)))

    def apply_vertical_offset(self, delta: float) -> None:
        """Move vertically from spawn base by ``delta`` (paired top/bottom use the same delta)."""
        self._y_float = self._base_y + delta
        self._position = (int(self._x_float), int(round(self._y_float)))

    @property
    def sprite(self):
        return self._sprite

    @property
    def position(self):
        return self._position

    def update(self) -> None:
        """Standalone oscillation (unused when spawner drives motion via apply_vertical_offset)."""
        if self._amplitude == 0.0:
            return
        self._time += self._frequency
        raw_y = self._base_y + self._amplitude * math.sin(self._time)
        clamped = max(self._min_y, min(raw_y, self._max_y))
        self._y_float = clamped
        self._position = (int(self._x_float), int(round(clamped)))
