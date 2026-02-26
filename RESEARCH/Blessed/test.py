import time
from blessed import Terminal

HEIGHT = 10
WIDTH = 20

def main():
    term = Terminal()  # Create a terminal control object for screen/input features.
    
    bird_y = HEIGHT // 2
    bird_x = WIDTH // 2
    
    # Hide cursor and clear screen once
    print(term.clear + term.hide_cursor, end="", flush=True)  # Clear the screen and hide the text cursor.
    
    def draw():
        output = term.home  # Move cursor to the top-left so each frame redraws in place.
        for y in range(HEIGHT):
            line = ""
            for x in range(WIDTH):
                if x == bird_x and y == bird_y:
                    line += "O"  # Bird
                else:
                    line += "."  # Background
            output += line + "\n"
        print(output, end="", flush=True)
    
    try:
        with term.cbreak(), term.raw():  # Enable immediate key reads and pass raw key sequences through.
            while True:
                # INPUT
                key = term.inkey(timeout=0.05)  # Read one key press from the terminal (non-blocking with timeout).
                if key and key.lower() == "w":  # Letter keys are read from key value (string), not key.code.
                    bird_y = max(0, bird_y - 1)
                elif key and key.lower() == "s":  # Move down with S.
                    bird_y = min(HEIGHT - 1, bird_y + 1)
                elif key and key.lower() == "a":  # Move left with A.
                    bird_x = max(0, bird_x - 1)
                elif key and key.lower() == "d":  # Move right with D.
                    bird_x = min(WIDTH - 1, bird_x + 1)
                elif key.code == term.KEY_UP:  # Compare pressed key code to terminal's Up Arrow constant.
                    bird_y = max(0, bird_y - 1)
                elif key.code == term.KEY_DOWN:  # Compare to terminal's Down Arrow constant.
                    bird_y = min(HEIGHT - 1, bird_y + 1)
                elif key.code == term.KEY_LEFT:  # Compare to terminal's Left Arrow constant.
                    bird_x = max(0, bird_x - 1)
                elif key.code == term.KEY_RIGHT:  # Compare to terminal's Right Arrow constant.
                    bird_x = min(WIDTH - 1, bird_x + 1)
                elif key == "\x1b":  # ESC
                    break
                
                # DRAW
                draw()
    finally:
        # Show cursor on exit
        print(term.show_cursor, end="", flush=True)  # Restore the text cursor before leaving.

if __name__ == "__main__":
    main()