"""
Creates and updates obstacle pairs (top + bottom) for the game.

The spawner:
  - Scrolls obstacles to the left each "frame"
  - Removes pairs that have moved fully off the left side of the screen
  - Spawns new pairs on a fixed schedule, up to a maximum count
  - Picks obstacle art and gap position using randomness (optionally seeded for testing)
"""

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from gameObjects.obstacle import Obstacle


# @dataclass auto-builds __init__ from the fields below (name, weight, ...).
@dataclass
class ObstacleTypeConfig:
    """One style of pipe pair: which images to use and how it may move."""

    name: str
    # Used for weighted random choice: higher weight = picked more often.
    weight: float
    # File paths for the top and bottom obstacle sprites (see Obstacle).
    top_sprite: str
    bottom_sprite: str
    # If amplitude is 0, obstacles stay at their spawn height.
    # If > 0, they bob up/down within min/max bounds (see Obstacle.update).
    amplitude: float = 0.0
    # How fast the sine wave advances each frame (only matters if amplitude > 0).
    frequency: float = 0.05  # radians per frame


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
        # How many character columns wide the terminal is (obstacles spawn just past the right edge).
        self._screen_width = screen_width
        # Usable vertical space for placing the gap (typically terminal height minus UI rows).
        self._game_height = game_height
        # Pixels (character columns) moved left per update() call.
        self._speed = obstacle_speed
        # Vertical space between top and bottom obstacles, in terminal rows.
        self._gap_size = gap_size
        # Spawn a new pair every this many calls to update() (e.g. 80 means every 80 frames).
        self._spawn_interval = spawn_interval
        # Cap on how many top+bottom pairs can exist at once.
        self._max_pairs = max_pairs
        # Random number generator; pass an int seed for reproducible runs/tests.
        self._rng = random.Random(rng_seed)

        # Turn weights like [3, 1] into probabilities [0.75, 0.25] for random.choices().
        total = sum(t.weight for t in obstacle_types)
        self._types = obstacle_types
        self._weights = [t.weight / total for t in obstacle_types]

        # Each item is (top_obstacle, bottom_obstacle) for one gap.
        self._pairs: List[Tuple[Obstacle, Obstacle]] = []
        # Increments once per update(); used with % to decide when to spawn.
        self._frame_counter: int = 0

        # Start with one pair on screen so the player is not waiting on an empty level.
        self._spawn_pair()

    @property
    def obstacles(self) -> List[Obstacle]:
        """Collision and drawing expect a single list: top1, bot1, top2, bot2, ..."""
        result = []
        for top, bot in self._pairs:
            result.append(top)
            result.append(bot)
        return result

    def update(self) -> None:
        """Call once per game tick: move obstacles, drop off-screen pairs, maybe spawn."""
        self._frame_counter += 1

        # Pairs still at least partly visible stay; fully off the left are dropped.
        survived: List[Tuple[Obstacle, Obstacle]] = []
        for top, bot in self._pairs:
            # Shared x so top and bottom stay aligned horizontally.
            new_x = top._x_float - self._speed
            top.set_x(new_x)
            bot.set_x(new_x)
            top.update()
            bot.update()
            # int(new_x) + top.width > 0 means some part of the obstacle is still on screen.
            if int(new_x) + top.width > 0:
                survived.append((top, bot))

        self._pairs = survived

        # Every spawn_interval frames, try to add another pair if under the cap.
        # % is remainder: True when frame_counter is 80, 160, 240, ... if interval is 80.
        if (
            self._frame_counter % self._spawn_interval == 0
            and len(self._pairs) < self._max_pairs
        ):
            self._spawn_pair()

    def _pick_type(self) -> ObstacleTypeConfig:
        """Pick one obstacle style at random, respecting weights."""
        # choices returns a list of length k=1; [0] is that single pick.
        return self._rng.choices(self._types, weights=self._weights, k=1)[0]

    def _spawn_pair(self) -> None:
        """Create one top+bottom pair off the right side with a random vertical gap."""
        cfg = self._pick_type()
        # Start just beyond the right edge so obstacles scroll into view.
        spawn_x = float(self._screen_width + 2)

        # Build temporary obstacles only to read how tall each sprite is (rows).
        top_tmp = Obstacle(spawn_x, 0, cfg.top_sprite)
        bot_tmp = Obstacle(spawn_x, 0, cfg.bottom_sprite)
        top_h = top_tmp.height
        bot_h = bot_tmp.height

        # Pick a random vertical position for the gap center so each pair feels different.
        # half_gap is half the gap in rows; // is integer division (whole number).
        half_gap = self._gap_size // 2
        lo = top_h + half_gap + 1
        hi = self._game_height - bot_h - half_gap - 1
        if lo >= hi:
            # Screen too small for the math; use a simpler minimum range.
            lo = top_h + 1
        gap_center = self._rng.randint(lo, max(lo, hi))

        # Place top sprite so its bottom sits above the gap; bottom sprite just below gap center.
        top_y = float(gap_center - half_gap - top_h)  # can be negative (clips off top)
        bot_y = float(gap_center + half_gap)

        # Limits for sine bobbing so obstacles do not cross into the gap or off-screen.
        top_min_y = float(-(top_h - 1))
        top_max_y = float(gap_center - half_gap - top_h + cfg.amplitude)
        bot_min_y = float(bot_y - cfg.amplitude)
        bot_max_y = float(self._game_height - bot_h)

        top = Obstacle(
            spawn_x, top_y, cfg.top_sprite,
            amplitude=cfg.amplitude,
            frequency=cfg.frequency,
            min_y=top_min_y,
            max_y=top_max_y,
        )
        bot = Obstacle(
            spawn_x, bot_y, cfg.bottom_sprite,
            amplitude=cfg.amplitude,
            frequency=cfg.frequency,
            min_y=bot_min_y,
            max_y=bot_max_y,
        )

        self._pairs.append((top, bot))
