package com.cs506.project3a;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * JPA repository for {@link Player} records.
 */
@Repository
public interface PlayerRepository extends JpaRepository<Player, Long> {
  /**
   * Find a player by their username.
   *
   * @param username unique username
   * @return matching player if found
   */
  Optional<Player> findByUsername(String username);

  /**
   * Retrieve all players sorted by high score in descending order.
   *
   * @return players ordered by high score descending
   */
  List<Player> findAllByOrderByHighScoreDesc();
}