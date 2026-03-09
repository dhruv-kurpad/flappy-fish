package com.cs506.project3a;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/players")
@CrossOrigin(origins = "*")
public class PlayerController {

    @Autowired
    private PlayerRepository playerRepository;

    /**
     * Endpoint to register a new player.
     */
    @GetMapping("/register")
    public String register(@RequestParam String name, @RequestParam String pwd) {
        if (playerRepository.findByUsername(name).isPresent()) {
            return "Registration Failed: Username '" + name + "' is already taken.";
        }

        Player newPlayer = new Player(name, pwd);
        playerRepository.save(newPlayer);
        return "Registration Successful! Player ID: " + newPlayer.getId();
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
     */
    @GetMapping("/login")
    public Map<String, Object> login(@RequestParam String name, @RequestParam String pwd) {
        Optional<Player> player = playerRepository.findByUsername(name);

        if (player.isEmpty()) {
            return Map.of(
                    "success", false,
                    "message", "Login Failed: Username not found."
            );
        }

        if (!player.get().getPassword().equals(pwd)) {
            return Map.of(
                    "success", false,
                    "message", "Login Failed: Incorrect password."
            );
        }

        return Map.of(
                "success", true,
                "message", "Login successful!",
                "username", player.get().getUsername(),
                "playerId", player.get().getId(),
                "highScore", player.get().getHighScore()
        );
    }

    /**
     * Update high score for a specific player.
     */
    @GetMapping("/updateScore")
    public String updateScore(@RequestParam String name, @RequestParam int score) {
        Optional<Player> playerOpt = playerRepository.findByUsername(name);
        if (playerOpt.isPresent()) {
            Player player = playerOpt.get();
            if (score > player.getHighScore()) {
                player.setHighScore(score);
                playerRepository.save(player);
                return "Score updated.";
            }
            return "Current record is higher.";
        }
        return "User not found.";
    }

    /**
     * Remove a user for testing purposes.
     */
    @GetMapping("/remove")
    public String removeUser(@RequestParam String name){
        Optional<Player> player = playerRepository.findByUsername(name);
        if(player.isEmpty()){
            return "No user with username '" + name + "' found.";
        }
        playerRepository.delete(player.get());
        return "User '" + name + "' removed successfully.";
    }
}