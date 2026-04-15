from blessed import Terminal
import sys
import time
import random
import subprocess
import threading
from pathlib import Path
from auth import get_leaderboard
from gameObjects.player import Player
from gameObjects.obstacle_spawner import ObstacleSpawner, ObstacleTypeConfig
from gameObjects.sprite import Sprite
from display import draw

ASSETS = Path(__file__).resolve().parent / "assets"
_SOUNDS = ASSETS / "sounds"


def _play_sfx(name: str):
    """Play a short WAV sound effect asynchronously (fire-and-forget)."""
    path = _SOUNDS / f"{name}.wav"
    if not path.exists():
        return
    if sys.platform == "darwin":
        cmd = ["afplay", str(path)]
    elif sys.platform == "win32":
        import winsound
        threading.Thread(
            target=lambda: winsound.PlaySound(str(path), winsound.SND_FILENAME),
            daemon=True,
        ).start()
        return
    else:
        cmd = ["aplay", str(path)]
    threading.Thread(
        target=lambda: subprocess.run(cmd, capture_output=True),
        daemon=True,
    ).start()
HEADER_LINES = 4  # number of lines the header occupies in display.py

# --- COLLISION HELPER ---
def check_collision(player, obs):
    px, py = player.position
    ox, oy = obs.position

    # Check if the player's bounding box overlaps with the obstacle's bounding box
    overlap_x = px < ox + obs.width and px + player.width > ox
    overlap_y = py < oy + obs.height and py + player.height > oy

    return overlap_x and overlap_y

def update_score(player, obstacle_pairs, passed_pairs, score):
    active_pairs = set()
    player_left_edge = player.position[0]

    for top, bot in obstacle_pairs:
        pair_id = id(top)
        active_pairs.add(pair_id)
        pair_right_edge = top.position[0] + top.width

        if pair_right_edge < player_left_edge and pair_id not in passed_pairs:
            score += 1
            passed_pairs.add(pair_id)

    passed_pairs.intersection_update(active_pairs)
    return score

def get_high_score(username):
    result = get_leaderboard()
    if not result.get("success"):
        return 0

    for player in result.get("players", []):
        if player.get("name") == username:
            return player.get("highScore", 0)

    return 0

def start_game_logic(username):
    term = Terminal()
    saved_high_score = get_high_score(username)

    # --- Create Game Objects ---
    player = Player(term.width // 2 - 7, term.height // 2)
    game_height = term.height - HEADER_LINES - 1

    obstacle_types = [
        ObstacleTypeConfig(
            name="static",
            weight=1.0,
            top_sprite=str(ASSETS / "tentacles_top.txt"),
            bottom_sprite=str(ASSETS / "tentacles_bottom.txt"),
        ),
        ObstacleTypeConfig(
            name="moving",
            weight=0.0,
            top_sprite=str(ASSETS / "tentacles_top.txt"),
            bottom_sprite=str(ASSETS / "tentacles_bottom.txt"),
            amplitude=4.0,
            frequency=0.05,
        ),
    ]

    spawner = ObstacleSpawner(
        screen_width=term.width,
        game_height=game_height,
        obstacle_types=obstacle_types,
        obstacle_speed=1,
        gap_size=16,
        spawn_interval=80,
        max_pairs=2,
    )

    # Game State
    bird_y_float = float(player.position[1])
    FRAME_SCALE = 60.0
    TARGET_FRAME_SECONDS = 1.0 / FRAME_SCALE
    gravity = 0.75 * FRAME_SCALE  # Convert to per-second (scaled for ~60fps baseline)
    velocity = 0.0

    # --- Delta Time for frame-rate independence ---
    last_frame_time = time.perf_counter()

    # --- Flap Cooldown State ---
    last_flap_time = 0.0
    flap_cooldown = 0.05

    # --- Jump sprite timer ---
    # Counts down from JUMP_SPRITE_FRAMES to 0; while > 0 the jump sprite is shown.
    JUMP_SPRITE_FRAMES = 0.5
    _jump_sprite_timer = 0

    # --- Fish bubble particle system ---
    # Each entry: [x: float, y: float, vy: float, lifetime: int]
    # x/y are float world positions; vy is upward drift speed (rows/frame);
    # every frame x decreases by spawner._speed (same as obstacles).
    bubbles: list = []
    _bubble_frame = 0   # frame counter used to throttle trail emission

    # --- Ambient decorative bubble system ---
    # Clusters of bubbles spawn from the right edge and scroll left like obstacles.
    # Each entry: [x: float, y: float, vy: float, char: str]
    # char is 'O' (large), 'o' (small), or '.' (tiny).
    ambient_bubbles: list = []
    _ambient_frame = 0
    _next_ambient_spawn = random.randint(40, 80)  # frames until next cluster

    # --- Decorative jellyfish system ---
    # Each jellyfish: [x, y, frame, jump_timer, jump_cooldown, vy]
    #   frame 0 = jellyfish.txt (idle), frame 1 = jellyfishJump.txt (thrust)
    #   jump_timer  > 0 while thrust sprite is shown
    #   jump_cooldown counts down to the next thrust trigger
    #   vy is current vertical velocity (negative = upward in terminal coords)
    jf_sprites = [
        Sprite(str(ASSETS / "jellyfish.txt")).display,
        Sprite(str(ASSETS / "jellyfishJump.txt")).display,
    ]
    jf_idle_h  = len(jf_sprites[0])   # height of the idle sprite (for bubble spawn)
    jf_idle_w  = len(jf_sprites[0][0])
    jellyfishes: list = []
    jf_bubbles:  list = []   # [x, y, vy, lifetime]  vy starts downward then reverses
    _jf_spawn_timer = 0
    _next_jf_spawn  = random.randint(8, 10) * FRAME_SCALE

    # --- Decorative crab system ---
    # Two sprite frames alternate every 3 ticks; crabs scroll left slightly
    # faster than obstacles and are pinned to the bottom of the game area.
    # Each entry: [x: float, frame: int, frame_timer: int]
    crab_frames = [
        Sprite(str(ASSETS / "crabAnim_01.txt")).display,
        Sprite(str(ASSETS / "crabAnim_02.txt")).display,
    ]
    crab_height = len(crab_frames[0])
    crab_width  = len(crab_frames[0][0])
    crab_y      = game_height - crab_height   # pinned to the bottom row
    crabs: list = []
    _crab_spawn_timer  = 0
    _next_crab_spawn   = random.randint(10, 12) * FRAME_SCALE

    is_running = True

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        print(term.clear + term.hide_cursor, end="", flush=True)

        # --- PREGAME OVERLAY ---
        draw(player, spawner.obstacles, score=0, high_score=saved_high_score, term=term,
             bubbles=[], ambient_bubbles=[], crabs=[], crab_frames=crab_frames, crab_y=crab_y,
             jellyfishes=[], jf_sprites=jf_sprites, jf_bubbles=[])
        popup = " PRESS SPACE BAR TO BEGIN "
        x_pos = term.width // 2 - len(popup) // 2
        y_pos = term.height // 2
        print(term.move_xy(x_pos, y_pos) + term.black_on_cyan(popup), end="", flush=True)

        waiting = True
        while waiting:
            key = term.inkey()
            if key == ' ':
                _play_sfx("bubble")
                velocity = -2.5
                last_flap_time = time.time()
                waiting = False
            elif key.code == term.KEY_ESCAPE or key == 'q':
                return 0
        # --- END PREGAME OVERLAY ---

        score = 0
        passed_pairs = set()
        just_increased_difficulty = False
        while is_running:
            # Calculate delta time
            current_frame_time = time.perf_counter()
            dt = current_frame_time - last_frame_time
            last_frame_time = current_frame_time
            dt = min(dt, 0.05)  # Cap at 50ms to prevent huge jumps

            prev_y = player.position[1]

            # 1. PHYSICS UPDATE (Player)
            velocity += gravity * dt
            bird_y_float += velocity * dt

            # 2. INPUT
            key = term.inkey(timeout=0.03)
            current_time = time.time()

            if key == ' ':
                _play_sfx("bubble")
                if current_time - last_flap_time > flap_cooldown:
                    velocity = -10 * FRAME_SCALE * dt  # Convert to per-second units
                    last_flap_time = current_time
                # Switch to jump sprite and reset the display timer
                player.set_jumping(True)
                _jump_sprite_timer = JUMP_SPRITE_FRAMES * FRAME_SCALE
                # Flap burst: 5 bubbles scatter from around the fish body
                for _ in range(5):
                    bx = float(player.position[0]) + random.randint(-1, player.width // 2)
                    by = float(player.position[1]) + random.randint(0, player.height - 1)
                    vy = random.uniform(0.5, 0.9)
                    bubbles.append([bx, by, vy, 80])
            elif key.code == term.KEY_ESCAPE or key == 'q':
                is_running = False

            while term.inkey(timeout=0):
                pass

            # 3. BOUNDARY CHECKS (Player)
            if bird_y_float >= term.height - player.height:
                bird_y_float = float(term.height - player.height)
                is_running = False

            if bird_y_float < 1:
                bird_y_float = 1.0
                velocity = 0

            # 4. UPDATE PLAYER
            player._position = (player.position[0], int(bird_y_float))

            # 5. UPDATE OBSTACLES & CHECK COLLISIONS
            spawner.update()
            for obs in spawner.obstacles:
                if check_collision(player, obs):
                    is_running = False
            # 6. UPDATE SCORE
            score = update_score(player, spawner._pairs, passed_pairs, score)

            # 7. CHECK DIFFICULTY INCREASE
            if score % 5 == 0 and score > 0 and not just_increased_difficulty:
                new_speed = spawner._speed + 0.2
                new_interval = max(0, spawner._spawn_interval - 10)
                spawner.update_obstacle_speed(new_speed)
                spawner.update_spawn_interval(new_interval)
                just_increased_difficulty = True

                if score % 10 == 0:
                    for obs_type in spawner._types:
                        if obs_type.name == "moving":
                            new_weight = min(obs_type.weight + 0.2, 0.4)
                            obs_type.update_weight(new_weight)
            elif score % 5 != 0:
                just_increased_difficulty = False

            # 8. UPDATE JUMP SPRITE TIMER
            if _jump_sprite_timer > 0:
                _jump_sprite_timer -= dt * FRAME_SCALE
                if _jump_sprite_timer <= 0:
                    player.set_jumping(False)

            # 9. UPDATE FISH BUBBLE PARTICLES
            # Trail: one bubble every 3 frames from the fish's left edge (wake side)
            _bubble_frame += dt * FRAME_SCALE
            while _bubble_frame >= FRAME_SCALE:
                _bubble_frame -= FRAME_SCALE
                bx = float(player.position[0]) + random.randint(-1, 0)
                by = float(player.position[1]) + random.randint(0, player.height - 1)
                bubbles.append([bx, by, 0.3, 100])

            speed = spawner._speed

            # Advance fish bubbles: scroll left + drift upward + age
            live = []
            for b in bubbles:
                b[0] -= speed * dt * FRAME_SCALE * 0.25
                b[1] -= b[2] * dt * FRAME_SCALE * 0.25
                b[3] -= dt * FRAME_SCALE  # Convert to time-based (60fps reference)
                if b[3] > 0 and b[1] > 0:
                    live.append(b)
            bubbles = live

            # 10. UPDATE AMBIENT DECORATIVE BUBBLES
            _ambient_frame += dt * FRAME_SCALE
            if _ambient_frame >= _next_ambient_spawn:
                _ambient_frame = 0
                _next_ambient_spawn = random.randint(40, 80)

                # Cluster spawns in the lower half of the game area
                base_x = float(term.width + 2)
                base_y = float(random.randint(int(game_height * 0.50), int(game_height * 0.88)))

                # 1–2 large bubbles at the front of the cluster (leftmost → arrive first)
                for i in range(random.randint(1, 2)):
                    ambient_bubbles.append([
                        base_x + random.uniform(-1.0, 1.0),
                        base_y + random.uniform(-1.0, 1.0),
                        random.uniform(0.15, 0.25),
                        'O',
                    ])

                # 2–4 small bubbles trailing slightly behind
                for i in range(random.randint(2, 4)):
                    ambient_bubbles.append([
                        base_x + random.uniform(2.0, 8.0),
                        base_y + random.uniform(-2.0, 2.0),
                        random.uniform(0.20, 0.35),
                        'o',
                    ])

                # 1–2 tiny bubbles scattered further behind
                for i in range(random.randint(1, 2)):
                    ambient_bubbles.append([
                        base_x + random.uniform(4.0, 12.0),
                        base_y + random.uniform(-3.0, 3.0),
                        random.uniform(0.28, 0.45),
                        '.',
                    ])

            # Advance ambient bubbles: same world scroll + their own upward drift
            live_ambient = []
            for b in ambient_bubbles:
                b[0] -= speed * dt * FRAME_SCALE * 0.25
                b[1] -= b[2] * dt * FRAME_SCALE * 0.25
                if b[0] > -2 and b[1] > 0:
                    live_ambient.append(b)
            ambient_bubbles = live_ambient

            # 11. UPDATE DECORATIVE JELLYFISH
            _jf_spawn_timer += dt * FRAME_SCALE
            if _jf_spawn_timer >= _next_jf_spawn:
                _jf_spawn_timer = 0
                _next_jf_spawn = random.randint(8, 10) * FRAME_SCALE
                spawn_y = float(random.randint(int(game_height * 0.35), int(game_height * 0.75)))
                # [x, y, frame, jump_timer, jump_cooldown, vy]
                # Start with vy = 0; gravity will slowly pull down until first thrust.
                jellyfishes.append([float(term.width + 2), spawn_y, 0, 0,
                                    random.randint(15, 35), 0.0])

            jf_speed = spawner._speed
            JF_GRAVITY   = gravity  # rows/frame^2 — 1.5× slower slide-down
            JF_MAX_DRIFT = 0.30   # cap downward drift speed

            live_jf = []
            for jf in jellyfishes:
                jf[0] -= jf_speed * dt * FRAME_SCALE * 0.25   # scroll left at obstacle speed
                jf[1] += jf[5] * dt * FRAME_SCALE * 0.25     # apply current vy

                if jf[3] > 0:       # thrust animation in progress
                    jf[3] -= dt * FRAME_SCALE  # Convert to time-based
                    if jf[3] <= 0:  # thrust finished — revert to idle sprite
                        jf[2] = 0
                    # No gravity during thrust; vy holds at the burst value.
                else:
                    # Apply gravity: vy climbs toward JF_MAX_DRIFT (slide back down)
                    jf[5] = min(jf[5] + JF_GRAVITY * dt, JF_MAX_DRIFT)
                    jf[4] -= dt * FRAME_SCALE  # Convert to time-based
                    if jf[4] <= 0:  # trigger next thrust
                        jf[2] = 1
                        jf[3] = FRAME_SCALE
                        jf[5] = -0.75   # half of the original -1.5
                        jf[4] = random.randint(1, 3) * FRAME_SCALE
                        # Emit 5–8 thrust bubbles of varying size and spread
                        n = random.randint(5, 8)
                        for _ in range(n):
                            bx  = float(jf[0] + jf_idle_w // 2 + random.randint(-3, 3))
                            by  = float(jf[1] + jf_idle_h)
                            vx  = random.uniform(-0.25, 0.25)   # horizontal spread
                            vy  = random.uniform(0.7, 1.8)      # downward speed
                            ch  = random.choice(['O', 'o', 'o']) # mostly small, some large
                            jf_bubbles.append([bx, by, vx, vy, ch])

                if jf[0] > -jf_idle_w and jf[1] > -jf_idle_h:
                    live_jf.append(jf)
            jellyfishes = live_jf

            # Update jellyfish thrust bubbles:
            # [x, y, vx, vy, char]
            # vy decelerates each frame; bubble is removed when vy reaches ~0
            # (no upward phase — just a quick downward burst that fades out).
            live_jf_bub = []
            for b in jf_bubbles:
                b[0] -= jf_speed * dt   # world scroll
                b[0] += b[2] * dt * FRAME_SCALE * 0.25      # own horizontal spread (vx)
                b[1] += b[3] * dt * FRAME_SCALE * 0.25      # move downward by vy
                b[3] -= 0.10 * dt * FRAME_SCALE * 0.5   # decelerate (time-based)
                if b[3] > 0.05 and b[0] > 0:   # delete when nearly stopped
                    live_jf_bub.append(b)
            jf_bubbles = live_jf_bub

            # 12. UPDATE DECORATIVE CRABS
            _crab_spawn_timer += dt * FRAME_SCALE
            if _crab_spawn_timer >= _next_crab_spawn:
                _crab_spawn_timer = 0
                _next_crab_spawn = random.randint(10, 16) * FRAME_SCALE
                crabs.append([float(term.width + 2), 0, 0])  # x, frame, frame_timer

            crab_speed = spawner._speed * 1.3
            live_crabs = []
            for c in crabs:
                c[0] -= crab_speed * dt * FRAME_SCALE * 0.25        # scroll left faster than obstacles
                c[2] += dt * FRAME_SCALE                # advance animation timer (time-based)
                if c[2] >= 5:                  # switch sprite every 3 frames
                    c[2] = 0
                    c[1] = 1 - c[1]      # toggle between frame 0 and 1
                if c[0] > -crab_width:
                    live_crabs.append(c)
            crabs = live_crabs

            # 12. RENDER
            current_high_score = max(saved_high_score, score)
            draw(
                player,
                spawner.obstacles,
                score=score,
                high_score=current_high_score,
                term=term,
                bubbles=bubbles,
                ambient_bubbles=ambient_bubbles,
                crabs=crabs,
                crab_frames=crab_frames,
                crab_y=crab_y,
                jellyfishes=jellyfishes,
                jf_sprites=jf_sprites,
                jf_bubbles=jf_bubbles,
            )
            

        # Game Over Pause
        game_over_text = " GAME OVER! "
        print(term.move_xy(term.width // 2 - len(game_over_text) // 2, term.height // 2) + term.red_on_black(game_over_text), end="", flush=True)
        time.sleep(2)

    print(term.clear + term.show_cursor, end="", flush=True)
    return score
