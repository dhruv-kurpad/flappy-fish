package com.cs506.project3a;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class Project3aApplicationTests {

    private PlayerController pc;
	/* Tests basic functionality of adding and removing users
	*/
	@Test
	void addUserTest() {
		//Adds first user
		pc.register("WittyName", "password");
		assert(pc.login("WittyName", "password").get("message").equals("Login successful!"));

        //Adds second user
		pc.register("newName", "1234");
		assert(pc.login("newName", "1234").get("message").equals("Login successful!"));

		//removes both
         pc.removeUser("WittyName");
	    pc.removeUser("newName");


	}

    // Tests if system correctly rejects adding a new user with an already taken Username
	@Test
	void sameUserTest() {
		//Tests if same object uploaded twice
		pc.register("WittyName", "password");
		assert(pc.register("WittyName", "password").equals("Registration Failed: Username 'WittyName' is already taken."));

        //Checks if same name diff password is still correctly rejected
		assert(pc.register("WittyName", "badPass").equals("Registration Failed: Username 'WittyName' is already taken."));

		 pc.removeUser("WittyName");

	}

	@Test
	void samePasswordTest(){

		pc.register("WittyName", "password");
		assert(pc.register("NewName", "password")== "Registration Successful! Player ID: " + "NewName");
		assert(pc.login("NewName", "password").get("message").equals("Login successful!"));
       
	     pc.removeUser("WittyName");
	     pc.removeUser("newName");


	}

    //Tests if the system correctly rejects entries with no username
	@Test
	void emptyUserTest() {

		//Tests that both the registration fxn reports an error and the database is unaffected
		assert(pc.register("", "password").equals("Registration Failed: Username can not be empty."));
		assert(pc.login("", "password").get("message").equals("Login Failed: Username not found."));

	}

    //Tests if the saystem correctly rejects entries with no Password
	@Test
	void emptyPasswordTest() {

		//Tests that both the registration fxn reports an error and the database is unaffected
		assert(pc.register("WittyName", "").equals("Registration Failed: Password can not be empty."));
		assert(pc.login("WittyName", "").get("message").equals("Login Failed: Username not found."));
	}

}
