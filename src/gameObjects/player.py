from gameObjects.game_object import GameObject

class Player(GameObject):
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
#\;,    ,;\\,;
# \\\;;:::::::o
# ///;;::::::::<
#/;' "/////''
        self._sprite = [
            ["\\", ";", ",", " ", " ", " ", " ", ",", ";", "\\", "\\", ",", ";", " ", " "],
            [" ", "\\", "\\", "\\", ";", ";", ":", ":", ":", ":", ":", ":", ":", "o", " "],
            [" ", "/", "/", "/", ";", ";", ":", ":", ":", ":", ":", ":", ":", ":", "<"],
            ["/", ";", "'", " ", '"', "/", "/", "/", "/", "/", "'", "'", " ", " ", " "]
        ]

    @property
    def sprite(self):
        return self._sprite

    def update(self) -> None:
        pass
        