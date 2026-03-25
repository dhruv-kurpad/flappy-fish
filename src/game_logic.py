from blessed import Terminal
import time
from gameObjects.player import Player
from gameObjects.obstacle import Obstacle
from display import draw

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

    # --- Flap Cooldown State ---
    last_flap_time = 0.0
    flap_cooldown = 0.25  # Requires 1/4 second between flaps

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
            current_time = time.time()
            
            if key == ' ':
                # Only apply velocity if the cooldown has passed
                if current_time - last_flap_time > flap_cooldown:
                    velocity = -1.5 
                    last_flap_time = current_time
            elif key.code == term.KEY_ESCAPE or key == 'q':
                is_running = False
                
            # Drain the input buffer: deletes any extra queued-up keystrokes
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

            # 5. UPDATE OBSTACLES (The Scrolling Logic)
            for i, obs in enumerate(obstacles):
                prev_obs_x = obs.position[0]
                
                # Move the obstacle left
                obs_x_floats[i] -= obstacle_speed
                new_x_int = int(obs_x_floats[i])
                
                # If it moves off the left edge, respawn it on the right
                if new_x_int <= 1:
                    obs_x_floats[i] = float(term.width - obs.width - 2)
                    new_x_int = int(obs_x_floats[i])
                
                # Update object position
                obs._position = (new_x_int, obs.position[1])

            # 6. RENDER
            draw(player, obstacles, score=0, high_score=0, term=term)

            time.sleep(0.02)

        # Game Over Pause
        game_over_text = " GAME OVER! "
        print(term.move_xy(term.width // 2 - len(game_over_text) // 2, term.height // 2) + term.red_on_black(game_over_text), end="", flush=True)
        time.sleep(2) 

    print(term.clear, end="", flush=True)