package com.cs506.project3a;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface PlayerRepository extends JpaRepository<Player, Long> {
    // Custom query to find a player by username for duplicate checking
    Optional<Player> findByUsername(String username);
}