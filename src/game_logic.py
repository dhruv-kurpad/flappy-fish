from blessed import Terminal
import time
from pathlib import Path
from auth import get_leaderboard
from gameObjects.player import Player
from gameObjects.obstacle_spawner import ObstacleSpawner, ObstacleTypeConfig
from display import draw

ASSETS = Path(__file__).resolve().parent / "assets"
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
    gravity = 0.5
    velocity = 0.0

    # --- Flap Cooldown State ---
    last_flap_time = 0.0
    flap_cooldown = .05

    # --- Bubble Display time --- #
    last_space_press = 0.0
    bubble_display_time = 0.25  
    display_bubbles = False

    is_running = True

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        print(term.clear + term.hide_cursor, end="", flush=True)

        # --- PREGAME OVERLAY ---
        draw(player, spawner.obstacles, score=0, high_score=saved_high_score, term=term, disp_bubbles=False)
        popup = " PRESS SPACE BAR TO BEGIN "
        x_pos = term.width // 2 - len(popup) // 2
        y_pos = term.height // 2
        print(term.move_xy(x_pos, y_pos) + term.black_on_cyan(popup), end="", flush=True)

        waiting = True
        while waiting:
            key = term.inkey()
            if key == ' ':
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
            prev_y = player.position[1]

            # 1. PHYSICS UPDATE (Player)
            velocity += gravity
            bird_y_float += velocity

            # 2. INPUT
            key = term.inkey(timeout=0.03)
            current_time = time.time()

            if key == ' ':
                if current_time - last_flap_time > flap_cooldown:
                    velocity = -2.5
                    last_flap_time = current_time
                last_space_press = current_time
                display_bubbles = True
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
            # 6. UPDATE BUBBLES
            if current_time - last_space_press > bubble_display_time:
                display_bubbles = False
            # 7. UPDATE SCORE
            score = update_score(player, spawner._pairs, passed_pairs, score)
            # 8. Check for difficulty increase
            if score % 10 == 0 and score > 0 and not just_increased_difficulty:
                new_speed = spawner._speed + 0.2
                new_interval = max(30, spawner._spawn_interval - 4)
                spawner.update_obstacle_speed(new_speed)
                spawner.update_spawn_interval(new_interval)
                just_increased_difficulty = True

                if score % 20 == 0:
                    for obs_type in spawner._types:
                        if obs_type.name == "moving":
                            new_weight = min(obs_type.weight + 0.1, 0.4)
                            obs_type.update_weight(new_weight)
            elif score % 10 != 0:
                just_increased_difficulty = False
            # 8. RENDER
            current_high_score = max(saved_high_score, score)
            draw(player, spawner.obstacles, score=score, high_score=current_high_score, term=term, disp_bubbles=display_bubbles)

            time.sleep(0.01)

        # Game Over Pause
        game_over_text = " GAME OVER! "
        print(term.move_xy(term.width // 2 - len(game_over_text) // 2, term.height // 2) + term.red_on_black(game_over_text), end="", flush=True)
        time.sleep(2)

    print(term.clear + term.show_cursor, end="", flush=True)
    return score
