"""
Creates and updates obstacle pairs (top + bottom) and optional solo sprites (e.g. jellyfish).

Pairs share horizontal motion; when ``amplitude > 0``, both pieces share one vertical phase.
Solo obstacles (``solo=True``) spawn one sprite that bobs with the same phase logic.
"""

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from gameObjects.obstacle import JellyfishObstacle, Obstacle, Tentacle


@dataclass
class ObstacleTypeConfig:
    """Tentacle pair (default) or a single bobbing sprite (``solo=True``)."""

    name: str
    weight: float
    top_sprite: str
    bottom_sprite: str = ""
    solo: bool = False
    amplitude: float = 0.0
    frequency: float = 0.05

    def update_weight(self, new_weight: float) -> None:
        self.weight = new_weight


@dataclass
class SpawnedPair:
    """One top+bottom pair sharing scroll and optional shared vertical motion."""

    top: Obstacle
    bot: Obstacle
    amplitude: float
    frequency: float
    phase: float = 0.0


@dataclass
class SpawnedSolo:
    """One obstacle (e.g. jellyfish) with sine bobbing."""

    obs: Obstacle
    amplitude: float
    frequency: float
    phase: float = 0.0


class ObstacleSpawner:
    """Owns tentacle pairs and solo obstacles: scroll, bobbing, spawn, prune."""

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
        # Max concurrent spawn groups (each pair OR each solo counts as one).
        self._max_groups = max_pairs
        self._rng = random.Random(rng_seed)

        self._types = obstacle_types

        self._pair_list: List[SpawnedPair] = []
        self._solo_list: List[SpawnedSolo] = []
        self._frame_counter: int = 0

        self._spawn()

    def _group_count(self) -> int:
        return len(self._pair_list) + len(self._solo_list)

    @property
    def _pairs(self) -> List[Tuple[Obstacle, Obstacle]]:
        """(top, bot) only — used for pipe pass scoring (excludes jellyfish solos)."""
        return [(p.top, p.bot) for p in self._pair_list]

    @property
    def obstacles(self) -> List[Obstacle]:
        result: List[Obstacle] = []
        for pair in self._pair_list:
            result.append(pair.top)
            result.append(pair.bot)
        for solo in self._solo_list:
            result.append(solo.obs)
        return result

    def update(self) -> None:
        self._frame_counter += 1

        survived_pairs: List[SpawnedPair] = []
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
                survived_pairs.append(pair)

        self._pair_list = survived_pairs

        survived_solo: List[SpawnedSolo] = []
        for solo in self._solo_list:
            new_x = solo.obs._x_float - self._speed
            solo.obs.set_x(new_x)

            amp = float(solo.amplitude)
            if amp > 0.0:
                solo.phase += float(solo.frequency)
                delta = amp * math.sin(solo.phase)
                solo.obs.apply_vertical_offset(delta)

            if isinstance(solo.obs, JellyfishObstacle):
                solo.obs.tick_animation()

            if int(new_x) + solo.obs.width > 0:
                survived_solo.append(solo)

        self._solo_list = survived_solo

        if (
            self._frame_counter % self._spawn_interval == 0
            and self._group_count() < self._max_groups
        ):
            self._spawn()

    def _pick_type(self) -> ObstacleTypeConfig:
        weights = [max(0.0, t.weight) for t in self._types]
        return self._rng.choices(self._types, weights=weights, k=1)[0]

    def _spawn(self) -> None:
        cfg = self._pick_type()
        if cfg.solo:
            self._spawn_solo(cfg)
        else:
            self._spawn_tentacle_pair(cfg)

    def _spawn_tentacle_pair(self, cfg: ObstacleTypeConfig) -> None:
        spawn_x = float(self._screen_width + 2)

        top_tmp = Tentacle(spawn_x, 0, cfg.top_sprite)
        bot_tmp = Tentacle(spawn_x, 0, cfg.bottom_sprite)
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

        top = Tentacle(spawn_x, top_y, cfg.top_sprite, amplitude=0.0, frequency=0.0)
        bot = Tentacle(spawn_x, bot_y, cfg.bottom_sprite, amplitude=0.0, frequency=0.0)

        self._pair_list.append(
            SpawnedPair(
                top=top,
                bot=bot,
                amplitude=float(cfg.amplitude),
                frequency=float(cfg.frequency),
            )
        )

    def _spawn_solo(self, cfg: ObstacleTypeConfig) -> None:
        spawn_x = float(self._screen_width + 2)
        tmp = JellyfishObstacle(spawn_x, 0.0, cfg.top_sprite)
        h = tmp.height
        margin = 1
        y_lo = margin
        y_hi = max(margin, self._game_height - h - margin)
        base_y = float(self._rng.randint(y_lo, y_hi)) if y_lo <= y_hi else float(margin)

        obs = JellyfishObstacle(
            spawn_x,
            base_y,
            cfg.top_sprite,
            amplitude=0.0,
            frequency=0.0,
        )

        self._solo_list.append(
            SpawnedSolo(
                obs=obs,
                amplitude=float(cfg.amplitude),
                frequency=float(cfg.frequency),
            )
        )

    def update_obstacle_speed(self, new_speed: float) -> None:
        self._speed = new_speed

    def update_spawn_interval(self, new_interval: int) -> None:
        self._spawn_interval = new_interval
