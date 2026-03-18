from gameObjects.game_object import GameObject
from gameObjects.sprite import Sprite
from pathlib import Path

# Obstacle Class, inherits from GameObject
# Properties:
#  - position: Tuple[int, int] (x and y coordinates of the obstacle)
#  - sprite: List[List[str]] (2D array representing the visual representation of the obstacle)
class Obstacle(GameObject):
    def __init__(self, x: int, y: int, top: bool):
        self._position = (x, y)
        sprite_path = Path(__file__)
        if top:
            sprite_path = sprite_path.resolve().parent.parent / "assets" / "tentacles_top.txt"
        else:
            sprite_path = sprite_path.resolve().parent.parent / "assets" / "tentacles_bottom.txt"
        self._sprite = Sprite(str(sprite_path))
    
    @property
    def sprite(self):
        return self._sprite
    
    @property
    def position(self):
        return self._position

    def update(self) -> None:
        pass
