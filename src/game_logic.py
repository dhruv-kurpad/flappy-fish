from blessed import Terminal
import time
from gameObjects.player import Player
from gameObjects.obstacle import Obstacle
from display import draw

# Helper function to draw multi-line sprites
"""
def render_sprite(term, game_obj, color_func):
    x, y = game_obj.position
    for row_idx, row in enumerate(game_obj.sprite.display):
        line_str = "".join(row)
        # Only draw if it's within the terminal screen to avoid text wrapping bugs
        if 0 <= int(x) < term.width - len(line_str):
            print(term.move_xy(int(x), int(y) + row_idx) + color_func(line_str), end="", flush=True)

# Helper function to erase the old multi-line sprite
def erase_sprite(term, game_obj, old_x, old_y):
    spaces = " " * game_obj.width
    for row_idx in range(game_obj.height):
        if 0 <= int(old_x) < term.width - len(spaces):
            print(term.move_xy(int(old_x), int(old_y) + row_idx) + spaces, end="", flush=True)
"""

def start_game_logic(username):
    term = Terminal()
    
    # --- Create Game Objects ---
    player = Player(10, term.height // 2)
    obstacles = [
        Obstacle(term.width - 25, 0, top=True),
        Obstacle(term.width - 25, term.height - 12, top=False) 
    ]
    
    # Game State 
    bird_y_float = float(player.position[1])
    gravity = 0.15      
    velocity = 0.0
    
    # Obstacle State (Track their X positions as floats for smooth scrolling)
    obstacle_speed = 0.8
    obs_x_floats = [float(obs.position[0]) for obs in obstacles]

    is_running = True

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        print(term.clear, end="", flush=True) 
        
        while is_running:
            prev_y = player.position[1]

            # 1. PHYSICS UPDATE (Player)
            velocity += gravity
            bird_y_float += velocity
            
            # 2. INPUT
            key = term.inkey(timeout=0.03) 
            if key == ' ':
                velocity = -1.5 
            elif key.code == term.KEY_ESCAPE or key == 'q':
                is_running = False

            # 3. BOUNDARY CHECKS (Player)
            if bird_y_float >= term.height - player.height:
                bird_y_float = float(term.height - player.height)
                is_running = False 
            
            if bird_y_float < 1:
                bird_y_float = 1.0
                velocity = 0

            # 4. UPDATE & RENDER PLAYER
            player._position = (player.position[0], int(bird_y_float))
            current_y_int = player.position[1]
            
            """
            if current_y_int != prev_y:
                erase_sprite(term, player, player.position[0], prev_y)
                render_sprite(term, player, term.yellow)
            else:
                render_sprite(term, player, term.yellow)
            """

            # 5. UPDATE & RENDER OBSTACLES (The Scrolling Logic)
            for i, obs in enumerate(obstacles):
                prev_obs_x = obs.position[0]
                
                # Move the obstacle left
                obs_x_floats[i] -= obstacle_speed
                new_x_int = int(obs_x_floats[i])
                
                # Only redraw if the integer position changed
                if new_x_int != prev_obs_x:
                    """erase_sprite(term, obs, prev_obs_x, obs.position[1])"""
                    
                    # If it moves off the left edge, respawn it on the right
                    if new_x_int <= 1:
                        obs_x_floats[i] = float(term.width - obs.width - 2)
                        new_x_int = int(obs_x_floats[i])
                    
                    # Update object position and render
                    obs._position = (new_x_int, obs.position[1])
                    """render_sprite(term, obs, term.green)"""

            # 6. UI OVERLAY
            #print(term.move_xy(0, 0) + term.white_on_blue(f" Fisherman: {username} | SPACE to Swim | ESC to Quit "), end="", flush=True)
            draw(player, obstacles, score=0, high_score=0, term=term)

            time.sleep(0.02)

        # Game Over Pause
        game_over_text = " GAME OVER! "
        print(term.move_xy(term.width // 2 - len(game_over_text) // 2, term.height // 2) + term.red_on_black(game_over_text), end="", flush=True)
        time.sleep(2) 

    print(term.clear, end="", flush=True)