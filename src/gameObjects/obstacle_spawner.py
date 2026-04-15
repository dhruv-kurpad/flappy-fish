"""
Creates and updates obstacle pairs (top + bottom) for the game.

The spawner:
  - Scrolls obstacles to the left each "frame"
  - Removes pairs that have moved fully off the left side of the screen
  - Spawns new pairs on a fixed schedule, up to a maximum count
  - Picks obstacle art and gap position using randomness (optionally seeded for testing)

Paired obstacles (e.g. tentacles) share one horizontal position. When ``amplitude > 0``,
both sprites use the same vertical phase so they move together and the gap size stays fixed.
"""

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from gameObjects.obstacle import Obstacle


@dataclass
class ObstacleTypeConfig:
    """One style of pipe pair: which images to use and how it may move."""

    name: str
    weight: float
    top_sprite: str
    bottom_sprite: str
    # If 0, the pair is static. If > 0, both pieces move together by amplitude * sin(phase).
    amplitude: float = 0.0
    frequency: float = 0.05  # radians added to shared phase each frame

    def update_weight(self, new_weight: float) -> None:
        self.weight = new_weight


@dataclass
class SpawnedPair:
    """One top+bottom pair sharing scroll and (when moving) one vertical motion."""

    top: Obstacle
    bot: Obstacle
    amplitude: float
    frequency: float
    phase: float = 0.0


class ObstacleSpawner:
    """Owns all moving obstacle pairs: scrolling, spawning, and pruning."""

    def __init__(
        self,
        screen_width: int,
        game_height: int,
        obstacle_types: List[ObstacleTypeConfig],
        obstacle_speed: float = 0.8,
        gap_size: int = 12,
        spawn_interval: int = 80,
        max_pairs: int = 2,
        rng_seed: Optional[int] = None,
    ):
        self._screen_width = screen_width
        self._game_height = game_height
        self._speed = obstacle_speed
        self._gap_size = gap_size
        self._spawn_interval = spawn_interval
        self._max_pairs = max_pairs
        self._rng = random.Random(rng_seed)

        self._types = obstacle_types

        self._pair_list: List[SpawnedPair] = []
        self._frame_counter: int = 0

        self._spawn_pair()

    @property
    def _pairs(self) -> List[Tuple[Obstacle, Obstacle]]:
        """(top, bot) tuples for scoring and any code that expects the old layout."""
        return [(p.top, p.bot) for p in self._pair_list]

    @property
    def obstacles(self) -> List[Obstacle]:
        result = []
        for pair in self._pair_list:
            result.append(pair.top)
            result.append(pair.bot)
        return result

    def update(self) -> None:
        self._frame_counter += 1

        survived: List[SpawnedPair] = []
        for pair in self._pair_list:
            top, bot = pair.top, pair.bot
            new_x = top._x_float - self._speed
            top.set_x(new_x)
            bot.set_x(new_x)

            amp = float(pair.amplitude)
            if amp > 0.0:
                pair.phase += float(pair.frequency)
                delta = amp * math.sin(pair.phase)
                top.apply_vertical_offset(delta)
                bot.apply_vertical_offset(delta)

            if int(new_x) + top.width > 0:
                survived.append(pair)

        self._pair_list = survived

        if (
            self._frame_counter % self._spawn_interval == 0
            and len(self._pair_list) < self._max_pairs
        ):
            self._spawn_pair()

    def _pick_type(self) -> ObstacleTypeConfig:
        # Use current weights so difficulty tweaks via update_weight() apply.
        weights = [max(0.0, t.weight) for t in self._types]
        return self._rng.choices(self._types, weights=weights, k=1)[0]

    def _spawn_pair(self) -> None:
        cfg = self._pick_type()
        spawn_x = float(self._screen_width + 2)

        top_tmp = Obstacle(spawn_x, 0, cfg.top_sprite)
        bot_tmp = Obstacle(spawn_x, 0, cfg.bottom_sprite)
        top_h = top_tmp.height
        bot_h = bot_tmp.height

        half_gap = self._gap_size // 2
        lo = half_gap + 1
        hi = self._game_height - half_gap - 1
        if lo >= hi:
            lo = top_h + 1
        gap_center = self._rng.randint(lo, max(lo, hi))

        top_y = float(gap_center - half_gap - top_h)
        bot_y = float(gap_center + half_gap)

        # Motion is driven by SpawnedPair (shared phase); keep Obstacle internal amplitude at 0.
        top = Obstacle(spawn_x, top_y, cfg.top_sprite, amplitude=0.0, frequency=0.0)
        bot = Obstacle(spawn_x, bot_y, cfg.bottom_sprite, amplitude=0.0, frequency=0.0)

        self._pair_list.append(
            SpawnedPair(
                top=top,
                bot=bot,
                amplitude=float(cfg.amplitude),
                frequency=float(cfg.frequency),
            )
        )

    def update_obstacle_speed(self, new_speed: float) -> None:
        self._speed = new_speed

    def update_spawn_interval(self, new_interval: int) -> None:
        self._spawn_interval = new_interval
