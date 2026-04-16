package com.cs506.project3a;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class Project3aApplicationTests {

  @Autowired
  private PlayerController pc;

  @Test
  void addUserTest() {
    assert (pc.register("WittyName", "password") == 0);
    assert ((int) pc.login("WittyName", "password").get("code") == 0);

    assert (pc.register("newName", "1234") == 0);
    assert ((int) pc.login("newName", "1234").get("code") == 0);

    pc.removeUser("WittyName");
    pc.removeUser("newName");
  }

  @Test
  void sameUserTest() {
    pc.register("WittyName", "password");
    assert (pc.register("WittyName", "password") == -1);
    assert (pc.register("WittyName", "badPass") == -1);

    pc.removeUser("WittyName");
  }

  @Test
  void samePasswordTest() {
    pc.register("WittyName", "password");
    assert (pc.register("NewName", "password") == 0);
    assert ((int) pc.login("NewName", "password").get("code") == 0);

    pc.removeUser("WittyName");
    pc.removeUser("NewName");
  }

  @Test
  void emptyUserTest() {
    assert (pc.register("", "password") == -2);
    assert ((int) pc.login("", "password").get("code") == -1);
  }

  @Test
  void emptyPasswordTest() {
    assert (pc.register("WittyName", "") == -3);
    assert ((int) pc.login("WittyName", "").get("code") == -1);
  }

  //Test if the score is updated properly if it is greater than previous values
  @Test
  void updateScoreTest(){
    pc.register("WittyName", "pwd");
    pc.updateScore("WittyName", 5);
    assert (pc.getScore("WittyName") == 5);
    pc.updateScore("WittyName", 7);
    assert (pc.getScore("WittyName") == 7);
    pc.removeUser("WittyName");
  }

  //Test for get all Players
  @Test
  void getAllPlayersTest(){
    int numPlayersBefore = pc.getAllPlayers().size();
    pc.register("WittyName", "pwd");
    assert(pc.getAllPlayers().size() == numPlayersBefore +1);
    pc.removeUser("WittyName");
  }
}
