import math
import random
from pathlib import Path
from gameObjects.game_object import GameObject
from gameObjects.sprite import Sprite

_ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _pad_display_rows(rows, target_h: int, target_w: int):
    """Pad a list of char rows to a fixed size (same as decorative jellyfish-era sprites)."""
    out = []
    for i in range(target_h):
        if i < len(rows):
            r = rows[i][:]
            while len(r) < target_w:
                r.append(" ")
            out.append(r)
        else:
            out.append([" "] * target_w)
    return out


def _match_sprite_dimensions(a: Sprite, b: Sprite) -> None:
    """Resize both displays so width/height match (avoids draw/collision glitches when swapping)."""
    ha, wa = len(a.display), len(a.display[0])
    hb, wb = len(b.display), len(b.display[0])
    th, tw = max(ha, hb), max(wa, wb)
    a.display = _pad_display_rows(a.display, th, tw)
    b.display = _pad_display_rows(b.display, th, tw)


class Obstacle(GameObject):
    """Shared logic for anything the player can hit (pipes, jellyfish, etc.)."""

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


class Tentacle(Obstacle):
    """One vertical half of a tentacle pipe pair (top or bottom sprite)."""


class JellyfishObstacle(Obstacle):
    """
    Solo jellyfish hazard: spawner scrolls and bobs it; thrust animation matches
    the old decorative system (idle ↔ jump sprite on a timer).
    """

    JUMP_SPRITE_FRAMES = 8

    def __init__(
        self,
        x: float,
        y: float,
        sprite_path,
        amplitude: float = 0.0,
        frequency: float = 0.0,
        min_y: float = 0.0,
        max_y: float = 0.0,
        jump_sprite_path=None,
    ):
        jump = jump_sprite_path or str(_ASSETS / "jellyfishJump.txt")
        super().__init__(x, y, sprite_path, amplitude, frequency, min_y, max_y)
        self._sprite_idle = self._sprite
        self._sprite_jump = Sprite(jump)
        _match_sprite_dimensions(self._sprite_idle, self._sprite_jump)
        # Drive which frame is shown (same logic shape as decorative jellyfish)
        self._jump_timer = 0
        self._jump_cooldown = random.randint(15, 35)

    @property
    def sprite(self) -> Sprite:
        if self._jump_timer > 0:
            return self._sprite_jump
        return self._sprite_idle

    def tick_animation(self) -> None:
        """
        Call once per frame after movement. Mirrors decorative behaviour:
        show thrust sprite for JUMP_SPRITE_FRAMES ticks, then idle until cooldown elapses.
        """
        if self._jump_timer > 0:
            self._jump_timer -= 1
        else:
            self._jump_cooldown -= 1
            if self._jump_cooldown <= 0:
                self._jump_timer = self.JUMP_SPRITE_FRAMES
                self._jump_cooldown = random.randint(15, 35)
