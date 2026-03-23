from typing import Tuple
from gameObjects.sprite import Sprite
from abc import ABC, abstractmethod

# GameObject Class, abstract base class for all game objects
# Properties:
# - position: Tuple[int, int] (x and y coordinates of the object)
# - sprite: List[List[str]] (2D array representing the visual representation of the object)
class GameObject(ABC):
    @property
    def position(self) -> Tuple[float, float]:
        raise NotImplementedError
    
    @property
    def sprite(self) -> Sprite:
        raise NotImplementedError
    
    @property
    def width(self) -> int:
        return len(self.sprite.display[0]) if self.sprite.display else 0
    
    @property
    def height(self) -> int:
        return len(self.sprite.display) if self.sprite.display else 0
    
    @abstractmethod
    def update(self) -> None:
        raise NotImplementedError
