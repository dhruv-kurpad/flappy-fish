package com.cs506.project3a;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/players")
public class PlayerController {

    @Autowired
    private PlayerRepository playerRepository;

    // Endpoint to register a new player via URL parameters
    // Example: /api/players/register?name=user1&pwd=abc
    @GetMapping("/register")
    public String register(@RequestParam String name, @RequestParam String pwd) {
        // Business Logic: Check if username already exists in database
        if (playerRepository.findByUsername(name).isPresent()) {
            return "Registration Failed: Username '" + name + "' is already taken.";
        }

        // If not taken, save the new player
        Player newPlayer = new Player(name, pwd);
        playerRepository.save(newPlayer);
        return "Registration Successful! Player ID: " + newPlayer.getId();
    }

    // Endpoint to list all players for debugging
    @GetMapping("/all")
    public List<Player> getAllPlayers() {
        return playerRepository.findAll();
    }

    // Endpoint to validate login credentials
    // Example: /api/players/login?name=user1&pwd=abc
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
                "playerId", player.get().getId()
        );
    }
}