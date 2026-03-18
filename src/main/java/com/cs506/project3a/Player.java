package com.cs506.project3a;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * Entity class representing a player in the game.
 */
@Entity
@Table(name = "players")
public class Player {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  // The unique=true constraint prevents duplicate usernames at the database level
  @Column(nullable = false, unique = true)
  private String username;

  @Column(nullable = false)
  private String password;

  @Column(name = "high_score")
  private Integer highScore = 0;

  /** Default constructor required by JPA. */
  public Player() {}

  /**
   * Constructs a Player with the given username and password.
   */
  public Player(String username, String password) {
    this.username = username;
    this.password = password;
    this.highScore = 0;
  }

  public Long getId() {
    return id;
  }

  public String getUsername() {
    return username;
  }

  public void setUsername(String username) {
    this.username = username;
  }

  public String getPassword() {
    return password;
  }

  public void setPassword(String password) {
    this.password = password;
  }

  public Integer getHighScore() {
    return highScore;
  }

  public void setHighScore(Integer highScore) {
    this.highScore = highScore;
  }
}
