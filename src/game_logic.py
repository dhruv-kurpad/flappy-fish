from blessed import Terminal
import time

def start_game_logic(username):
    term = Terminal()
    
    # Game State 
    bird_y = float(term.height // 2)
    bird_x = 10
    gravity = 0.15      
    velocity = 0.0
    is_running = True

    prev_y = int(bird_y)

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        # Add end="" and flush=True to every print statement
        print(term.clear, end="", flush=True) 
        
        while is_running:
            # 1. PHYSICS UPDATE
            velocity += gravity
            bird_y += velocity
            
            # 2. INPUT
            key = term.inkey(timeout=0.04) 
            if key == ' ':
                velocity = -1.2 
            elif key.code == term.KEY_ESCAPE or key == 'q':
                is_running = False

            # 3. BOUNDARY CHECKS
            # Stop right above the bottom edge of the terminal
            if bird_y >= term.height - 2:
                bird_y = float(term.height - 2)
                is_running = False # Hit the floor = Game Over
            
            # Stop at the UI bar
            if bird_y < 1:
                bird_y = 1.0
                velocity = 0

            # 4. RENDERING
            current_y_int = int(bird_y)
            
            if current_y_int != prev_y:
                # Erase old position
                print(term.move_xy(bird_x, prev_y) + "      ", end="", flush=True)
                # Draw new position
                print(term.move_xy(bird_x, current_y_int) + term.yellow(">(o )"), end="", flush=True)
                prev_y = current_y_int
            else:
                # Redraw safely
                print(term.move_xy(bird_x, current_y_int) + term.yellow(">(o )"), end="", flush=True)

            # 5. UI OVERLAY
            print(term.move_xy(0, 0) + term.white_on_blue(f" Player: {username} | SPACE to Flap | ESC to Quit "), end="", flush=True)
            
            time.sleep(0.02)

        # Game Over Pause
        game_over_text = " GAME OVER! "
        print(term.move_xy(term.width // 2 - len(game_over_text) // 2, term.height // 2) + term.red_on_black(game_over_text), end="", flush=True)
        time.sleep(2) # Pause for 2 seconds so the player can see they died

    print(term.clear, end="", flush=True)