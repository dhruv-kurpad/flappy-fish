package com.cs506.project3a;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * REST controller for player management operations.
 */
@RestController
@RequestMapping("/api/players")
@CrossOrigin(origins = "*")
public class PlayerController {

  @Autowired
  private PlayerRepository playerRepository;

  /**
   * Endpoint to register a new player.
   * Returns: 0 = success, -1 = username already taken
   */
  @GetMapping("/register")
  public int register(@RequestParam String name, @RequestParam String pwd) {
    if (name == null || name.isBlank()) {
      return -2;
    }
    if (pwd == null || pwd.isBlank()) {
      return -3;
    }
    if (playerRepository.findByUsername(name).isPresent()) {
      return -1;
    }

    Player newPlayer = new Player(name, pwd);
    playerRepository.save(newPlayer);
    return 0;
  }

  /**
   * Endpoint to list all players for debugging.
   */
  @GetMapping("/all")
  public List<Player> getAllPlayers() {
    return playerRepository.findAll();
  }

  /**
   * Endpoint to retrieve the leaderboard sorted by high score.
   */
  @GetMapping("/leaderboard")
  public List<Player> getLeaderboard() {
    return playerRepository.findAllByOrderByHighScoreDesc();
  }

  /**
   * Endpoint to validate login credentials.
   * Returns code: 0 = success, -1 = username not found, -2 = incorrect password
   */
  @GetMapping("/login")
  public Map<String, Object> login(@RequestParam String name, @RequestParam String pwd) {
    Optional<Player> player = playerRepository.findByUsername(name);

    if (player.isEmpty()) {
      return Map.of("code", -1);
    }

    if (!player.get().getPassword().equals(pwd)) {
      return Map.of("code", -2);
    }

    return Map.of(
        "code", 0,
        "username", player.get().getUsername(),
        "playerId", player.get().getId(),
        "highScore", player.get().getHighScore()
    );
  }

  /**
   * Update high score for a specific player.
   * Returns: 0 = score updated, 1 = current record is higher, -1 = user not found
   */
  @GetMapping("/updateScore")
  public int updateScore(@RequestParam String name, @RequestParam int score) {
    Optional<Player> playerOpt = playerRepository.findByUsername(name);
    if (playerOpt.isPresent()) {
      Player player = playerOpt.get();
      if (score > player.getHighScore()) {
        player.setHighScore(score);
        playerRepository.save(player);
        return 0;
      }
      return 1;
    }
    return -1;
  }

  /**
   * Remove a user for testing purposes.
   * Returns: 0 = removed successfully, -1 = user not found
   */
  @GetMapping("/remove")
  public int removeUser(@RequestParam String name) {
    Optional<Player> player = playerRepository.findByUsername(name);
    if (player.isEmpty()) {
      return -1;
    }
    playerRepository.delete(player.get());
    return 0;
  }
}
