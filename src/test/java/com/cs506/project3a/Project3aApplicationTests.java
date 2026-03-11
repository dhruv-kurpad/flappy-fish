package com.cs506.project3a;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;

@SpringBootTest
class Project3aApplicationTests {

    private PlayerController pc;
	/* Tests basic functionality of adding and removing users
	*/
	@Test
	void addUserTest() {
		//Adds first user
		Player testUser = new Player("WittyName", "password");
		pc.register(testUser);
		assert(pc.getUserByName("WittyName") == testUser.getUsername());

        //Adds second user
		Player nextUser = new Player("newName", "1234");
		pc.register(nextUser);
		assert(pc.getUserByName("newName") == nextUser.getUsername());

		//removes both
         pc.removeUser("WittyName");
	    pc.removeUser("newName");

		assert(pc.getAllPlayers == NULL);

	}

    // Tests if system correctly rejects adding a new user with an already taken Username
	@Test
	void sameUserTest() {
		//Tests if same object uploaded twice
		Player testUser = new Player("WittyName", "password");
		pc.register(testUser);
		assert(pc.register(testUser).equals("Registration Failed: Username 'WittyName' is already taken."));

        //Checks if same name diff password is still correctly rejected
        Player sameName = new Player("WittyName", "badPass");
		assert(pc.register(sameName).equals("Registration Failed: Username 'WittyName' is already taken."));

		 pc.removeUser("WittyName");

	}

	@Test
	void samePasswordTest(){

		Player testUser = new Player("WittyName", "password");
		Player newUser = new Player("NewName", "password");
		pc.register(testUser);
		assert(pc.register(newUser)== "Registration Successful! Player ID: " + newUser.getId());
		assert(pc.getUserByName("NewName") == testUser.getUsername());
       
	     pc.removeUser("WittyName");
	     pc.removeUser("newName");


	}

    //Tests if the system correctly rejects entries with no username
	@Test
	void emptyUserTest() {

		//Tests that both the registration fxn reports an error and the database is unaffected
		Player testUser = new Player("", "password");
		assert(pc.register(testUser).equals("Registration Failed: Username can not be empty."));
		assert(pc.getAllPlayers == NULL);

	}

    //Tests if the saystem correctly rejects entries with no Password
	@Test
	void emptyPasswordTest() {

		//Tests that both the registration fxn reports an error and the database is unaffected
		Player testUser = new Player("WittyName", "");
		assert(pc.register(testUser).equals("Registration Failed: Password can not be empty."));
		assert(pc.getAllPlayers == NULL);
	}

}
