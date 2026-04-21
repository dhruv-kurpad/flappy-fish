from gameObjects.game_object import GameObject
from gameObjects.sprite import Sprite
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Player Class, inherits from GameObject
# Properties:
#  - position: Tuple[int, int] (x and y coordinates of the player)
#  - sprite: List[List[str]] (2D array representing the visual representation of the player)
class Player(GameObject):
    def __init__(self, x: float, y: float):
        self._position = (x, y)
        self._normal_sprite = Sprite(str(_ASSETS / "fish.txt"))
        self._jump_sprite   = Sprite(str(_ASSETS / "fishJump.txt"))
        self._dead_sprite   = Sprite(str(_ASSETS / "fishDead.txt"))
        self._sprite = self._normal_sprite

    @property
    def sprite(self):
        return self._sprite

    @property
    def position(self):
        return self._position

    def set_jumping(self, jumping: bool) -> None:
        """Switch between the jump sprite and the normal idle sprite."""
        self._sprite = self._jump_sprite if jumping else self._normal_sprite

    def set_dead(self, dead: bool) -> None:
        """Switch between the jump sprite and the normal idle sprite."""
        self._sprite = self._dead_sprite if dead else self._normal_sprite

    @property
    def is_dead(self) -> bool:
        return self._sprite is self._dead_sprite

    def update(self) -> None:
        pass
        