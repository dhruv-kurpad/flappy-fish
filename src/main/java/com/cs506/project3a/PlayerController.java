package com.cs506.project3a;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

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
}