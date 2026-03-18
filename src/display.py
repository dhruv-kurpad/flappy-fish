from typing import List, Tuple
from blessed import Terminal
from gameObjects.obstacle import Obstacle
from gameObjects.player import Player

# Dimensions of the game area
HEIGHT = 24
WIDTH = 100

# Header template for the game display
# XX and YY are placeholders for score and high score, respectively
HEADER = ("----------------------------------------------------------------------------------------------------\n"
          "Score: XX                              Flappy Fisherman                               High Score: YY\n"
          "----------------------------------------------------------------------------------------------------\n")

# Renders the game state to the terminal
# Parameters:
# - player: Player object representing the player's character
# - obstacles: List of Obstacle objects representing the obstacles in the game
# - score: Current score of the player
# - high_score: Highest score achieved by the player
# - term: Terminal object from the blessed library for controlling terminal output
def draw(player: Player, obstacles: List[Obstacle], score: int, high_score: int, term: Terminal):
    output = term.home

    # Addscore and high score to header
    updated_header = HEADER.replace("XX", str(score) if score >= 10 else "0" + str(score)).replace("YY", str(high_score) if high_score >= 10 else "0" + str(high_score))
    output += updated_header

    # Draw the game area with player and obstacles
    for y in range(HEIGHT):
        line = ""
        for x in range(WIDTH):
            if x >= player.position[0] and x < player.position[0] + player.width and y >= player.position[1] and y < player.position[1] + player.height:
                line += player.sprite.display[y - player.position[1]][x - player.position[0]]
            elif any(x >= obs.position[0] and x < obs.position[0] + obs.width and y >= obs.position[1] and y < obs.position[1] + obs.height for obs in obstacles):
                obs = next(obs for obs in obstacles if x >= obs.position[0] and x < obs.position[0] + obs.width and y >= obs.position[1] and y < obs.position[1] + obs.height)
                line += obs.sprite.display[y - obs.position[1]][x - obs.position[0]]
            else:
                line += " "
        output += line + "\n"
    print(output, end="", flush=True)

# Example use case for testing the draw function
if __name__ == "__main__":
    term = Terminal()
    player = Player(10, 5)
    score = 10
    high_score = 8
    obstacles = [Obstacle(70, 19, False), Obstacle(70, -5, True)]
    draw(player, obstacles, score, high_score, term)
    