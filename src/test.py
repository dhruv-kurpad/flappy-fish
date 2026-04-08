import unittest

from blessed import Terminal
from pathlib import Path
from gameObjects.obstacle import Obstacle
from gameObjects.player import Player
from gameObjects.sprite import Sprite
from display import _ASSETS, draw

class TestFrontend(unittest.TestCase):

    def test_pipe(self):
        """Test to see if pipeline works"""
        self.assertEqual(True, True)
    
    def test_Sprite(self):
        sprite = Sprite(Path(__file__).resolve().parent / "assets" / "fish.txt")
        self.assertTrue(isinstance(sprite.display, list))
    
    def test_sprite_content(self):
        sprite = Sprite(Path(__file__).resolve().parent / "assets" / "fish.txt")
        expected_sprite = [
            ['\\', ';', ',', ' ', ' ', ' ', ' ', ',', ';', '\\', '\\', ',', ';', ' ', ' '],
            [' ', '\\', '\\', '\\', ';', ';', ':', ':', ':', ':', ':', ':', ':', 'o', ' '],
            [' ', '/', '/', '/', ';', ';', ':', ':', ':', ':', ':', ':', ':', ':', '<'],
            ['/', ';', '\'', ' ', '"', '/', '/', '/', '/', '/', '\'', '\'', ' ', ' ', ' '],
        ]
        self.assertEqual(sprite.display, expected_sprite)

    def test_player(self):
        player = Player(10, 5)
        self.assertTrue(isinstance(player, Player))
    
    def test_player_position(self):
        player = Player(10, 5)
        self.assertEqual(player.position, (10, 5))
    
    def test_player_sprite(self):
        player = Player(10, 5)
        expected_sprite = Sprite(Path(__file__).resolve().parent / "assets" / "fish.txt").display
        self.assertEqual(player.sprite.display, expected_sprite)
    
    def test_obstacle(self):
        obstacle_bottom = Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        self.assertTrue(isinstance(obstacle_bottom, Obstacle))
        obstacle_top = Obstacle(70, -5, str(_ASSETS / "tentacles_top.txt"))
        self.assertTrue(isinstance(obstacle_top, Obstacle))
    
    def test_obstacle_position(self):
        obstacle_bottom = Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        self.assertEqual(obstacle_bottom.position, (70, 10))
        obstacle_top = Obstacle(70, -5, str(_ASSETS / "tentacles_top.txt"))
        self.assertEqual(obstacle_top.position, (70, -5))
    
    def test_obstacle_sprite(self):
        obstacle_bottom = Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        expected_sprite_bottom = Sprite(Path(__file__).resolve().parent / "assets" / "tentacles_bottom.txt").display
        self.assertEqual(obstacle_bottom.sprite.display, expected_sprite_bottom)
        obstacle_top = Obstacle(70, -5, str(_ASSETS / "tentacles_top.txt"))
        expected_sprite_top = Sprite(Path(__file__).resolve().parent / "assets" / "tentacles_top.txt").display
        self.assertEqual(obstacle_top.sprite.display, expected_sprite_top)
    
    def test_draw(self):
        term = Terminal()
        player = Player(10.4, 5.5)
        score = 10
        high_score = 8
        obstacles = [Obstacle(70, 19, str(_ASSETS / "tentacles_bottom.txt")), Obstacle(70, -5, str(_ASSETS / "tentacles_top.txt"))]
        try:
            draw(player, obstacles, score, high_score, term, disp_bubbles=False)
            self.assertTrue(True)  # If no exceptions are raised, the test passes
        except Exception as e:
            self.fail(f"draw() raised an exception: {e}")
        

    

if __name__ == '__main__':
    unittest.main()
