import math
import random
from pathlib import Path
from typing import Optional, Tuple
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
    GRAVITY = 0.04 / 1.5
    MAX_DRIFT = 0.30
    THRUST_VY = -0.75

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
        self._vy = 0.0

    @property
    def sprite(self) -> Sprite:
        if self._jump_timer > 0:
            return self._sprite_jump
        return self._sprite_idle

    def update_swim(self) -> None:
        """Apply legacy jellyfish vertical thrust/gravity movement once per frame."""
        # Old game_logic order: first move by current vy, then update timers/forces.
        self._y_float += self._vy

        if self._jump_timer > 0:
            self._jump_timer -= 1
        else:
            self._vy = min(self._vy + self.GRAVITY, self.MAX_DRIFT)
            self._jump_cooldown -= 1
            if self._jump_cooldown <= 0:
                self._jump_timer = self.JUMP_SPRITE_FRAMES
                self._vy = self.THRUST_VY
                self._jump_cooldown = random.randint(30, 180)

        self._position = (int(self._x_float), int(round(self._y_float)))


class PufferfishObstacle(Obstacle):
    """
    Solo hazard: starts as the smallest sprite and advances through four stages as it
    scrolls toward the player. Each stage uses a larger sprite (top-left anchor; the
    hitbox grows downward as the art expands).
    """

    # >1.0 slows early stages slightly (1.0 = linear). Keep moderate so stages don’t bunch at the end.
    _INFLATION_EASE_POWER = 1.45

    def __init__(
        self,
        x: float,
        y: float,
        sprite_paths: Optional[Tuple[str, str, str, str]] = None,
        amplitude: float = 0.0,
        frequency: float = 0.0,
        min_y: float = 0.0,
        max_y: float = 0.0,
    ):
        paths = sprite_paths or tuple(str(_ASSETS / f"pufferfish{i}.txt") for i in range(1, 5))
        self._spawn_x = float(x)
        self._stage = 0
        super().__init__(x, y, paths[0], amplitude, frequency, min_y, max_y)
        self._sprites = [self._sprite] + [Sprite(p) for p in paths[1:]]

    @property
    def sprite(self) -> Sprite:
        return self._sprites[self._stage]

    def _set_stage(self, new_stage: int) -> None:
        new_stage = max(0, min(3, int(new_stage)))
        if new_stage == self._stage:
            return
        self._stage = new_stage
        self._position = (int(self._x_float), int(round(self._y_float)))

    def update_inflation(self, player_x: float, player_width: float = 0.0) -> None:
        """Advance sprite stage from scroll progress toward the player (call each frame)."""
        spawn_x = self._spawn_x
        x = self._x_float
        # p reaches 1 when the obstacle's left edge hits ``approach_end``. That point must be
        # near the player (not near spawn): if ``approach_end`` is too far right, ``total``
        # is tiny and inflation finishes in a few frames. Here, full size when the left edge
        # is just past the player’s right edge (still no AABB overlap: ox >= player_right).
        player_right = player_x + max(player_width, 1.0)
        ahead_end = player_right + 5.0
        approach_end = min(ahead_end, spawn_x - 6.0)
        total = spawn_x - approach_end
        if total <= 1e-6:
            total = 1.0
        traveled = spawn_x - x
        # Stay on sprite 1 for this much scroll before stages 2–4 use the rest of the path.
        start_delay = min(36.0, total * 0.14)
        delayed = max(0.0, traveled - start_delay)
        usable = max(total - start_delay, 1e-6)
        p_linear = max(0.0, min(1.0, delayed / usable))
        p = p_linear ** self._INFLATION_EASE_POWER
        new_stage = min(3, int(p * 4))
        self._set_stage(new_stage)
