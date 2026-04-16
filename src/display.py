from pathlib import Path
from typing import List, Tuple
from blessed import Terminal
from gameObjects.obstacle import JellyfishObstacle, Obstacle, PufferfishObstacle, Tentacle
from gameObjects.player import Player

_ASSETS = Path(__file__).resolve().parent / "assets"

# Renders the game state to the terminal
# Parameters:
# - player: Player object representing the player's character
# - obstacles: List of Obstacle objects representing the obstacles in the game
# - score: Current score of the player
# - high_score: Highest score achieved by the player
# - term: Terminal object from the blessed library for controlling terminal output
def draw(player: Player, obstacles: List[Obstacle], score: int, high_score: int, term: Terminal,
         bubbles: list = None, ambient_bubbles: list = None,
         crabs: list = None, crab_frames: list = None, crab_y: int = 0,
         jellyfishes: list = None, jf_sprites: list = None,
         jf_bubbles: list = None):
    output = term.home
    output += "\n"

    # Create header with score and high score, centered around the game title
    header = ("-" * term.width + "\n" +
              f"Score: {str(score).rjust(3, '0')}" + " " * (term.width // 2 - 18) + "Flappy Fisherman" + " " * (term.width // 2 - 23) + f"High Score: {str(high_score).rjust(3, '0')}\n" +
                "-" * term.width + "\n")

    output += header
    #Temporary code for now!
    WIDTH = term.width
    HEIGHT = term.height - len(header.split('\n')) - 1
    #Temporary code for now!

    # Fish trail/flap bubbles: O(1) set lookup, all render as 'o'
    bubble_set = {(round(b[0]), round(b[1])) for b in bubbles} if bubbles else set()

    # Decorative crabs: build (x, y) -> char from the current animation frame.
    # Spaces in the sprite are transparent (not added to the map).
    crab_map: dict = {}
    if crabs and crab_frames:
        for c in crabs:
            cx    = round(c[0])
            frame = crab_frames[c[1]]
            for row_i, row in enumerate(frame):
                ry = crab_y + row_i
                for col_i, ch in enumerate(row):
                    if ch != ' ':
                        crab_map[(cx + col_i, ry)] = ch

    # Jellyfish: build (x, y) -> char from the active sprite frame.
    # Spaces are transparent. Uses dim magenta (\033[2;35m) for a dark-purple look.
    jf_map: dict = {}
    if jellyfishes and jf_sprites:
        for jf in jellyfishes:
            cx, cy = round(jf[0]), round(jf[1])
            sprite  = jf_sprites[jf[2]]
            for row_i, row in enumerate(sprite):
                for col_i, ch in enumerate(row):
                    if ch != ' ':
                        jf_map[(cx + col_i, cy + row_i)] = ch

    # Jellyfish thrust bubbles: [x, y, vx, vy, char] — use char for size variation.
    # Later entries overwrite earlier ones if they round to the same cell (fine for decoration).
    jf_bubble_map: dict = {}
    if jf_bubbles:
        for b in jf_bubbles:
            jf_bubble_map[(round(b[0]), round(b[1]))] = b[4]

    # Ambient decorative bubbles: dict (x, y) -> char so each size renders correctly.
    ambient_map: dict = {}
    if ambient_bubbles:
        for b in ambient_bubbles:
            ambient_map[(round(b[0]), round(b[1]))] = b[3]

    # Jellyfish: bright pink (bold + 256-color) so it reads apart from yellow fish / green tentacles / red crab.
    BRIGHT_PINK = "\033[1;38;5;207m"
    RESET = "\033[0m"

    # Draw the game area — render priority (top = highest):
    #   Player > Crabs > Obstacles > Fish bubbles >
    #   Jellyfish > Jellyfish bubbles > Ambient bubbles
    for y in range(HEIGHT):
        line = ""
        for x in range(WIDTH):
            if (x >= round(player.position[0]) and x < round(player.position[0]) + player.width
                    and y >= round(player.position[1]) and y < round(player.position[1]) + player.height):
                # Player sprite — highest priority
                line += (f"{term.yellow}"
                         f"{player.sprite.display[y - round(player.position[1])][x - round(player.position[0])]}"
                         f"{term.normal}")
            elif (x, y) in crab_map:
                # Crab — in front of obstacles so it appears at the foreground bottom
                line += f"{term.red}{crab_map[(x, y)]}{term.normal}"
            elif any(x >= round(obs.position[0]) and x < round(obs.position[0]) + obs.width
                     and y >= round(obs.position[1]) and y < round(obs.position[1]) + obs.height
                     for obs in obstacles):
                # Obstacle sprite (tentacles = green; jellyfish obstacle = bright pink)
                obs = next(obs for obs in obstacles
                           if x >= round(obs.position[0]) and x < round(obs.position[0]) + obs.width
                           and y >= round(obs.position[1]) and y < round(obs.position[1]) + obs.height)
                ch = obs.sprite.display[y - round(obs.position[1])][x - round(obs.position[0])]
                if isinstance(obs, JellyfishObstacle):
                    line += f"{BRIGHT_PINK}{ch}{RESET}"
                elif isinstance(obs, PufferfishObstacle):
                    line += f"{term.yellow}{ch}{term.normal}"
                else:
                    line += f"{term.green}{ch}{term.normal}"
            elif (x, y) in bubble_set:
                # Fish trail / flap bubbles
                line += f"{term.cyan}o{term.normal}"
            elif (x, y) in jf_map:
                # Decorative jellyfish (if any) — match hazard pink
                line += f"{BRIGHT_PINK}{jf_map[(x, y)]}{RESET}"
            elif (x, y) in jf_bubble_map:
                # Jellyfish thrust bubbles — dim cyan (same darkness as jellyfish, blue colour)
                line += f"\033[2;36m{jf_bubble_map[(x, y)]}{RESET}"
            elif (x, y) in ambient_map:
                # Ambient decorative bubbles — background layer, lowest priority
                line += f"{term.cyan}{ambient_map[(x, y)]}{term.normal}"
            else:
                line += " "
        output += line + "\n"
    print(output + term.hide_cursor, end="", flush=True)

# Example use case for testing the draw function
if __name__ == "__main__":
    term = Terminal()
    player = Player(10.4, 5.5)
    score = 10
    high_score = 8
    obstacles = [
        Tentacle(70, 19, str(_ASSETS / "tentacles_bottom.txt")),
        Tentacle(70, -5, str(_ASSETS / "tentacles_top.txt")),
    ]
    draw(player, obstacles, score, high_score, term, bubbles=[], ambient_bubbles=[])
