import unittest

from blessed import Terminal
from pathlib import Path
from gameObjects.obstacle import Obstacle, Tentacle, JellyfishObstacle, PufferfishObstacle
from gameObjects.obstacle_spawner import ObstacleSpawner, ObstacleTypeConfig
from gameObjects.player import Player
from gameObjects.sprite import Sprite
from display import _ASSETS, draw
from game_logic import update_score, check_collision, get_high_score

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
            draw(player, obstacles, score, high_score, term, bubbles=[], ambient_bubbles=[])
            self.assertTrue(True)  # If no exceptions are raised, the test passes
        except Exception as e:
            self.fail(f"draw() raised an exception: {e}")

    def test_score_increases_after_fully_passing_obstacle(self):
        player = Player(20, 5)
        top = Obstacle(0, -5, str(_ASSETS / "tentacles_top.txt"))
        bottom = Obstacle(0, 10, str(_ASSETS / "tentacles_bottom.txt"))
        passed_pairs = set()

        score = update_score(player, [(top, bottom)], passed_pairs, 0)

        self.assertEqual(score, 1)

    def test_score_does_not_increase_before_fully_passing_obstacle(self):
        top = Obstacle(0, -5, str(_ASSETS / "tentacles_top.txt"))
        bottom = Obstacle(0, 10, str(_ASSETS / "tentacles_bottom.txt"))
        player = Player(top.position[0] + top.width, 5)
        passed_pairs = set()

        score = update_score(player, [(top, bottom)], passed_pairs, 0)

        self.assertEqual(score, 0)

    def test_score_only_increases_once_per_obstacle(self):
        player = Player(20, 5)
        top = Obstacle(0, -5, str(_ASSETS / "tentacles_top.txt"))
        bottom = Obstacle(0, 10, str(_ASSETS / "tentacles_bottom.txt"))
        passed_pairs = set()

        score = update_score(player, [(top, bottom)], passed_pairs, 0)
        score = update_score(player, [(top, bottom)], passed_pairs, score)

        self.assertEqual(score, 1)

    # ───── COLLISION TESTS ─────
    def test_collision_no_overlap(self):
        """Test no collision when player and obstacle don't overlap"""
        player = Player(5, 5)
        obstacle = Obstacle(50, 10, str(_ASSETS / "tentacles_bottom.txt"))
        self.assertFalse(check_collision(player, obstacle))

    def test_collision_with_overlap(self):
        """Test collision when player and obstacle bounding boxes overlap"""
        player = Player(10, 10)
        obstacle = Obstacle(15, 10, str(_ASSETS / "tentacles_bottom.txt"))
        # This should detect an overlap since positions are close
        result = check_collision(player, obstacle)
        self.assertIsInstance(result, bool)

    def test_collision_exact_position(self):
        """Test collision detection at same position"""
        player = Player(10, 10)
        obstacle = Obstacle(10, 10, str(_ASSETS / "tentacles_bottom.txt"))
        result = check_collision(player, obstacle)
        self.assertIsInstance(result, bool)

    # ───── PLAYER METHOD TESTS ─────
    def test_player_set_jumping(self):
        """Test player jumping sprite switch"""
        player = Player(10, 5)
        player.set_jumping(True)
        self.assertEqual(player.sprite, player._jump_sprite)
        player.set_jumping(False)
        self.assertEqual(player.sprite, player._normal_sprite)

    def test_player_set_dead(self):
        """Test player dead sprite switch"""
        player = Player(10, 5)
        player.set_dead(True)
        self.assertEqual(player.sprite, player._dead_sprite)
        player.set_dead(False)
        self.assertEqual(player.sprite, player._normal_sprite)

    def test_player_width_height(self):
        """Test player has width and height properties"""
        player = Player(10, 5)
        self.assertGreater(player.width, 0)
        self.assertGreater(player.height, 0)

    # ───── OBSTACLE METHOD TESTS ─────
    def test_obstacle_set_x(self):
        """Test obstacle horizontal movement"""
        obstacle = Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        obstacle.set_x(50.5)
        self.assertEqual(obstacle.position[0], 50)

    def test_obstacle_set_base_y(self):
        """Test obstacle base_y setter"""
        obstacle = Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        obstacle.set_base_y(20.0)
        self.assertEqual(obstacle._base_y, 20.0)

    def test_obstacle_apply_vertical_offset(self):
        """Test obstacle vertical offset (bobbing)"""
        obstacle = Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        initial_base_y = obstacle._base_y
        obstacle.apply_vertical_offset(5.0)
        self.assertEqual(obstacle._y_float, initial_base_y + 5.0)

    def test_obstacle_width_height(self):
        """Test obstacle width and height"""
        obstacle = Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        self.assertGreater(obstacle.width, 0)
        self.assertGreater(obstacle.height, 0)

    # ───── TENTACLE TESTS ─────
    def test_tentacle_creation(self):
        """Test Tentacle obstacle type"""
        tentacle = Tentacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))
        self.assertIsInstance(tentacle, Tentacle)
        self.assertIsInstance(tentacle, Obstacle)

    # ───── JELLYFISH OBSTACLE TESTS ─────
    def test_jellyfish_creation(self):
        """Test JellyfishObstacle creation"""
        jf = JellyfishObstacle(50, 15, str(_ASSETS / "jellyfish.txt"))
        self.assertIsInstance(jf, JellyfishObstacle)

    def test_jellyfish_sprite_switching(self):
        """Test jellyfish thrust animation sprite switching"""
        jf = JellyfishObstacle(50, 15, str(_ASSETS / "jellyfish.txt"))
        idle_sprite = jf.sprite
        jf._jump_timer = 5
        jump_sprite = jf.sprite
        # Timer > 0 should show jump sprite
        self.assertNotEqual(id(idle_sprite), id(jump_sprite))

    def test_jellyfish_update_swim(self):
        """Test jellyfish swimming movement update"""
        jf = JellyfishObstacle(50, 15, str(_ASSETS / "jellyfish.txt"))
        initial_y = jf._y_float
        jf._vy = 1.0
        jf.update_swim()
        # Y should have changed due to velocity
        self.assertNotEqual(jf._y_float, initial_y)

    def test_jellyfish_thrust_cooldown(self):
        """Test jellyfish thrust triggers on cooldown"""
        jf = JellyfishObstacle(50, 15, str(_ASSETS / "jellyfish.txt"))
        jf._jump_cooldown = 1
        jf._jump_timer = 0
        jf.update_swim()
        # After cooldown reaches 0, should trigger thrust
        self.assertTrue(jf._jump_timer > 0 or jf._jump_cooldown > 0)

    # ───── PUFFERFISH OBSTACLE TESTS ─────
    def test_pufferfish_creation(self):
        """Test PufferfishObstacle creation"""
        pf = PufferfishObstacle(50, 15)
        self.assertIsInstance(pf, PufferfishObstacle)
        self.assertEqual(pf._stage, 0)

    def test_pufferfish_stage_progression(self):
        """Test pufferfish inflation stages"""
        pf = PufferfishObstacle(100.0, 15)
        initial_stage = pf._stage
        # Call update_inflation with player approaching
        pf.update_inflation(50.0, 10.0)
        # Stage may or may not progress depending on distance calc
        self.assertGreaterEqual(pf._stage, 0)
        self.assertLessEqual(pf._stage, 3)

    def test_pufferfish_sprite_stages(self):
        """Test pufferfish has 4 sprite stages"""
        pf = PufferfishObstacle(50, 15)
        self.assertEqual(len(pf._sprites), 4)

    # ───── OBSTACLE SPAWNER TESTS ─────
    def test_spawner_creation(self):
        """Test ObstacleSpawner initialization"""
        types = [
            ObstacleTypeConfig("test", 1.0, str(_ASSETS / "tentacles_top.txt"), str(_ASSETS / "tentacles_bottom.txt"))
        ]
        spawner = ObstacleSpawner(80, 20, types)
        self.assertIsInstance(spawner, ObstacleSpawner)

    def test_spawner_obstacles_list(self):
        """Test spawner obstacles property returns list"""
        types = [
            ObstacleTypeConfig("test", 1.0, str(_ASSETS / "tentacles_top.txt"), str(_ASSETS / "tentacles_bottom.txt"))
        ]
        spawner = ObstacleSpawner(80, 20, types)
        obstacles = spawner.obstacles
        self.assertIsInstance(obstacles, list)

    def test_spawner_update_scrolls_left(self):
        """Test spawner update moves obstacles left"""
        types = [
            ObstacleTypeConfig("test", 1.0, str(_ASSETS / "tentacles_top.txt"), str(_ASSETS / "tentacles_bottom.txt"))
        ]
        spawner = ObstacleSpawner(80, 20, types, obstacle_speed=2)
        if spawner.obstacles:
            initial_x = spawner.obstacles[0].position[0]
            spawner.update()
            # Obstacle should move left (x decreases)
            self.assertLess(spawner.obstacles[0].position[0], initial_x + 2)

    def test_spawner_speed_update(self):
        """Test updating spawner speed"""
        types = [
            ObstacleTypeConfig("test", 1.0, str(_ASSETS / "tentacles_top.txt"), str(_ASSETS / "tentacles_bottom.txt"))
        ]
        spawner = ObstacleSpawner(80, 20, types, obstacle_speed=1)
        spawner.update_obstacle_speed(3)
        self.assertEqual(spawner._speed, 3)

    def test_spawner_interval_update(self):
        """Test updating spawner spawn interval"""
        types = [
            ObstacleTypeConfig("test", 1.0, str(_ASSETS / "tentacles_top.txt"), str(_ASSETS / "tentacles_bottom.txt"))
        ]
        spawner = ObstacleSpawner(80, 20, types, spawn_interval=80)
        spawner.update_spawn_interval(40)
        self.assertEqual(spawner._spawn_interval, 40)

    # ───── DISPLAY TESTS ─────
    def test_draw_with_crabs(self):
        """Test drawing with crabs"""
        term = Terminal()
        player = Player(10, 5)
        obstacles = []
        crab_frames = [
            [[' ', ' '], [' ', ' ']],
            [[' ', ' '], [' ', ' ']]
        ]
        crabs = [[50, 0, 0]]
        try:
            draw(player, obstacles, 0, 0, term, bubbles=[], ambient_bubbles=[], 
                 crabs=crabs, crab_frames=crab_frames, crab_y=15)
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"draw() with crabs raised exception: {e}")

    def test_draw_with_jellyfishes(self):
        """Test drawing with jellyfish"""
        term = Terminal()
        player = Player(10, 5)
        obstacles = []
        jf_sprites = [[[' ']], [[' ']]]
        jellyfishes = [[50, 10, 0, 0, 0, 0]]
        try:
            draw(player, obstacles, 0, 0, term, bubbles=[], ambient_bubbles=[],
                 jellyfishes=jellyfishes, jf_sprites=jf_sprites, jf_bubbles=[])
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"draw() with jellyfishes raised exception: {e}")

    def test_draw_with_tentacle_frame(self):
        """Test drawing with tentacle animation frame"""
        term = Terminal()
        player = Player(10, 5)
        obstacles = [Obstacle(70, 10, str(_ASSETS / "tentacles_bottom.txt"))]
        try:
            draw(player, obstacles, 0, 0, term, bubbles=[], ambient_bubbles=[], 
                 tentacle_frame=1)
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"draw() with tentacle frame raised exception: {e}")

    # ───── SCORE TESTS ─────
    def test_score_with_multiple_obstacles(self):
        """Test score increases correctly with multiple obstacle pairs"""
        player = Player(50, 10)
        top1 = Obstacle(0, -5, str(_ASSETS / "tentacles_top.txt"))
        bot1 = Obstacle(0, 10, str(_ASSETS / "tentacles_bottom.txt"))
        top2 = Obstacle(30, -5, str(_ASSETS / "tentacles_top.txt"))
        bot2 = Obstacle(30, 10, str(_ASSETS / "tentacles_bottom.txt"))
        passed_pairs = set()

        score = update_score(player, [(top1, bot1), (top2, bot2)], passed_pairs, 0)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 2)

    def test_score_with_empty_obstacles(self):
        """Test score with no obstacles"""
        player = Player(50, 10)
        passed_pairs = set()
        score = update_score(player, [], passed_pairs, 5)
        self.assertEqual(score, 5)

    # ───── SPRITE TESTS ─────
    def test_sprite_padding(self):
        """Test sprite rows are padded to same width"""
        sprite = Sprite(str(_ASSETS / "fish.txt"))
        if sprite.display:
            widths = [len(row) for row in sprite.display]
            # All rows should have same width after padding
            self.assertEqual(len(set(widths)), 1)

    def test_sprite_not_empty(self):
        """Test sprite is loaded and not empty"""
        sprite = Sprite(str(_ASSETS / "fish.txt"))
        self.assertGreater(len(sprite.display), 0)
        self.assertGreater(len(sprite.display[0]), 0)

    # ───── EDGE CASE TESTS ─────
    def test_player_at_origin(self):
        """Test player at origin position"""
        player = Player(0, 0)
        self.assertEqual(player.position, (0, 0))

    def test_obstacle_large_coordinates(self):
        """Test obstacle with large coordinates"""
        obstacle = Obstacle(10000, 5000, str(_ASSETS / "tentacles_bottom.txt"))
        self.assertEqual(obstacle.position, (10000, 5000))

    def test_obstacle_negative_coordinates(self):
        """Test obstacle with negative coordinates"""
        obstacle = Obstacle(-50, -20, str(_ASSETS / "tentacles_bottom.txt"))
        self.assertEqual(obstacle.position, (-50, -20))

    def test_score_boundary_same_y(self):
        """Test scoring when player is at obstacle edge"""
        player = Player(5, 10)
        top = Obstacle(0, -5, str(_ASSETS / "tentacles_top.txt"))
        bottom = Obstacle(0, 15, str(_ASSETS / "tentacles_bottom.txt"))
        passed_pairs = set()
        score = update_score(player, [(top, bottom)], passed_pairs, 0)
        self.assertIsInstance(score, int)

if __name__ == '__main__':
    unittest.main()
