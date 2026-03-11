from typing import List, Tuple
from blessed import Terminal
from gameObjects.player import Player


HEIGHT = 24
WIDTH = 100
HEADER = ("----------------------------------------------------------------------------------------------------\n"
          "Score: XX                              Flappy Fisherman                               High Score: YY\n"
          "----------------------------------------------------------------------------------------------------\n")

def draw(player: Player, score: int, high_score: int, term: Terminal):
    output = term.home
    updated_header = HEADER.replace("XX", str(score) if score >= 10 else "0" + str(score)).replace("YY", str(high_score) if high_score >= 10 else "0" + str(high_score))
    output += updated_header
    for y in range(HEIGHT):
        line = ""
        for x in range(WIDTH):
            if x >= player.x and x < player.x + player.width and y >= player.y and y < player.y + player.height():
                line += player.sprite[y - player.y][x - player.x]
            else:
                line += " "
        output += line + "\n"
    print(output, end="", flush=True)

if __name__ == "__main__":
    term = Terminal()
    player = Player(10, 10)
    score = 0
    high_score = 0
    draw(player, score, high_score, term)