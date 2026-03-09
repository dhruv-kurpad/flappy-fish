package com.cs506.project3a;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface PlayerRepository extends JpaRepository<Player, Long> {
    /**
     * Find a player by their username.
     * Used for login validation and duplicate checks.
     */
    Optional<Player> findByUsername(String username);

    /**
     * Retrieve all players sorted by high score in descending order.
     * Used for the game leaderboard.
     */
    List<Player> findAllByOrderByHighScoreDesc();
}