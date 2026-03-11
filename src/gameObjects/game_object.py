from typing import List, Tuple
from abc import ABC, abstractmethod

class GameObject(ABC):
    @property
    def position(self) -> Tuple[int, int]:
        raise NotImplementedError
    
    @property
    def sprite(self) -> List[List[str]]:
        raise NotImplementedError
    
    @property
    def width(self) -> int:
        return len(self.sprite[0]) if self.sprite else 0
    
    def height(self) -> int:
        return len(self.sprite) if self.sprite else 0
    
    @abstractmethod
    def update(self) -> None:
        raise NotImplementedError
