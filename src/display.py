from typing import List, Tuple
from blessed import Terminal
from gameObjects.obstacle import Obstacle
from gameObjects.player import Player

# Renders the game state to the terminal
# Parameters:
# - player: Player object representing the player's character
# - obstacles: List of Obstacle objects representing the obstacles in the game
# - score: Current score of the player
# - high_score: Highest score achieved by the player
# - term: Terminal object from the blessed library for controlling terminal output
def draw(player: Player, obstacles: List[Obstacle], score: int, high_score: int, term: Terminal):
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
    
    # Draw the game area with player and obstacles
    for y in range(HEIGHT):
        line = ""
        for x in range(WIDTH):
            if x >= round(player.position[0]) and x < round(player.position[0]) + player.width and y >= round(player.position[1]) and y < round(player.position[1]) + player.height:
                line += f"{term.yellow}{player.sprite.display[y - round(player.position[1])][x - round(player.position[0])]}{term.normal}"
            elif any(x >= round(obs.position[0]) and x < round(obs.position[0]) + obs.width and y >= round(obs.position[1]) and y < round(obs.position[1]) + obs.height for obs in obstacles):
                obs = next(obs for obs in obstacles if x >= round(obs.position[0]) and x < round(obs.position[0]) + obs.width and y >= round(obs.position[1]) and y < round(obs.position[1]) + obs.height)
                line += f"{term.green}{obs.sprite.display[y - round(obs.position[1])][x - round(obs.position[0])]}{term.normal}"
            else:
                line += " "
        output += line + "\n"
    print(output, end="", flush=True)

# Example use case for testing the draw function
if __name__ == "__main__":
    term = Terminal()
    player = Player(10.4, 5.5)
    score = 10
    high_score = 8
    obstacles = [Obstacle(70, 19, False), Obstacle(70, -5, True)]
    draw(player, obstacles, score, high_score, term)
    