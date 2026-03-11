from gameObjects.game_object import GameObject

# Player Class, inherits from GameObject
# Properties:
#  - position: Tuple[int, int] (x and y coordinates of the player)
#  - sprite: List[List[str]] (2D array representing the visual representation of the player)
class Player(GameObject):
    def __init__(self, x: int, y: int):
        self._position = (x, y)
        self._sprite = [
            ["\\", ";", ",", " ", " ", " ", " ", ",", ";", "\\", "\\", ",", ";", " ", " "],
            [" ", "\\", "\\", "\\", ";", ";", ":", ":", ":", ":", ":", ":", ":", "o", " "],
            [" ", "/", "/", "/", ";", ";", ":", ":", ":", ":", ":", ":", ":", ":", "<"],
            ["/", ";", "'", " ", '"', "/", "/", "/", "/", "/", "'", "'", " ", " ", " "]
        ]

    @property
    def sprite(self):
        return self._sprite
    
    @property
    def position(self):
        return self._position

    def update(self) -> None:
        pass
        