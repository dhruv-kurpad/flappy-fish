from pathlib import Path
from gameObjects.sprite import Sprite

_ASSETS = Path(__file__).resolve().parent.parent / "assets"


class Coin:
    """A collectible coin that scrolls left with obstacles.

    Each coin entry in game_logic is a Coin instance. On player collision the
    coin is marked ``collected`` so it is removed at the end of the frame and
    the score is incremented.
    """

    def __init__(self, x: float, y: float):
        self._x_float = x
        self._y_float = y
        self._sprite = Sprite(str(_ASSETS / "coin.txt"))
        self.collected = False

    @property
    def position(self):
        return (int(self._x_float), int(self._y_float))

    @property
    def width(self) -> int:
        return len(self._sprite.display[0]) if self._sprite.display else 0

    @property
    def height(self) -> int:
        return len(self._sprite.display) if self._sprite.display else 0

    @property
    def sprite(self) -> Sprite:
        return self._sprite

    def scroll(self, speed: float) -> None:
        """Advance the coin left by one frame's worth of scroll (matches obstacle movement)."""
        self._x_float -= speed
