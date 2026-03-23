from gameObjects.game_object import GameObject
from gameObjects.sprite import Sprite
from pathlib import Path

# Player Class, inherits from GameObject
# Properties:
#  - position: Tuple[int, int] (x and y coordinates of the player)
#  - sprite: List[List[str]] (2D array representing the visual representation of the player)
class Player(GameObject):
    def __init__(self, x: float, y: float):
        self._position = (x, y)
        sprite_path = Path(__file__).resolve().parent.parent / "assets" / "fish.txt"
        self._sprite = Sprite(str(sprite_path))

    @property
    def sprite(self):
        return self._sprite
    
    @property
    def position(self):
        return self._position

    def update(self) -> None:
        pass
        