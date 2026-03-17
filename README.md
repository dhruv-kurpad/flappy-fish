# Specification Document

Please fill out this document to reflect your team's project. This is a living document and will need to be updated regularly. You may also remove any section to its own document (e.g. a separate standards and conventions document), however you must keep the header and provide a link to that other document under the header.

Also, be sure to check out the Wiki for information on how to maintain your team's requirements.

## Team 3A

<!--The name of your team.-->

### Project Abstract

<!--A one paragraph summary of what the software will do.-->

Project description provided by course staff:  Players will navigate Fred the Fish through a series of underwater obstacles, using simple keyboard controls, where points are awarded the longer obstacles are avoided. Your task will include designing the game mechanics and creating ASCII art representations of the undersea environment  ([here]("https://github.com/schromya/FroggySecurity/blob/main/demo.gif") is an example of basic command-line ASCII art). Additionally, you will implement player accounts which enables a leaderboard system where players can view and compete for top scores.

### Customer

<!--A brief description of the customer for this software, both in general (the population who might eventually use such a system) and specifically for this document (the customer(s) who informed this document). Every project will have a customer from the CS506 instructional staff. Requirements should not be derived simply from discussion among team members. Ideally your customer should not only talk to you about requirements but also be excited later in the semester to use the system.-->

The customers for this software would be people who would want a fun game to play, and people who want to compete against others and their own scores.

### Specification

<!--A detailed specification of the system. UML, or other diagrams, such as finite automata, or other appropriate specification formalisms, are encouraged over natural language.-->

<!--Include sections, for example, illustrating the database architecture (with, for example, an ERD).-->

<!--Included below are some sample diagrams, including some example tech stack diagrams.-->

#### Technology Stack

```mermaid
flowchart RL
subgraph Front End
	A(Command Line)
end
	
subgraph Back End
	B(Java: SpringBoot)
end
	
subgraph Database
	C[(MySQL)]
end

A <--> B
B <--> C
```


#### Database

```mermaid
---
title: Draft Database Objects
---
erDiagram
    User {
        int user_id
        string name
        string password
        int high_score
    }

```

#### Class Diagram

WIP

```mermaid
---
title: Sample Class Diagram for Animal Program
---
classDiagram
    class Animal {
        - String name
        + Animal(String name)
        + void setName(String name)
        + String getName()
        + void makeSound()
    }
    class Dog {
        + Dog(String name)
        + void makeSound()
    }
    class Cat {
        + Cat(String name)
        + void makeSound()
    }
    class Bird {
        + Bird(String name)
        + void makeSound()
    }
    Animal <|-- Dog
    Animal <|-- Cat
    Animal <|-- Bird
```

#### Flowchart

```mermaid
---
title: Sample Program Flowchart
---
graph TD;
    Start([Start]) --> Login[/Login/];
    Login --> Get_Data[Get Data];
    Get_Data --> Validate_Data{Validate Data};
    Validate_Data -->|Valid| Play_Game[Go to Game];
    Validate_Data -->|Invalid| Error_Message[/Error Message/];
    Play_Game --> Finish_Game[Finish Game];
    Finish_Game --> Update_Score[Update Score];
    Update_Score --> End([End]);
    Error_Message --> End;
```

#### Behavior

WIP

```mermaid
---
title: Sample State Diagram For Coffee Application
---
stateDiagram
    [*] --> Ready
    Ready --> Brewing : Start Brewing
    Brewing --> Ready : Brew Complete
    Brewing --> WaterLowError : Water Low
    WaterLowError --> Ready : Refill Water
    Brewing --> BeansLowError : Beans Low
    BeansLowError --> Ready : Refill Beans
```

#### Sequence Diagram

WIP

```mermaid
sequenceDiagram

participant ReactFrontend
participant DjangoBackend
participant MySQLDatabase

ReactFrontend ->> DjangoBackend: HTTP Request (e.g., GET /api/data)
activate DjangoBackend

DjangoBackend ->> MySQLDatabase: Query (e.g., SELECT * FROM data_table)
activate MySQLDatabase

MySQLDatabase -->> DjangoBackend: Result Set
deactivate MySQLDatabase

DjangoBackend -->> ReactFrontend: JSON Response
deactivate DjangoBackend
```

### Standards & Conventions

<!--This is a link to a seperate coding conventions document / style guide-->
[Style Guide & Conventions](STYLE.md)

---

### Getting Started

### Running the Backend and MySQL (Local Docker)
Start the stack:

```bash
docker compose --profile dev up -d
```

- Spring Boot API: `http://localhost:8080`
- MySQL: `localhost:3306`, database `project3a_db`, user `root` / `root`

Helpful API calls:

```bash
# Register a player
curl "http://localhost:8080/api/players/register?name=string&pwd=string"

# List players
curl "http://localhost:8080/api/players/all"
```

Stop the stack:

```bash
docker compose --profile dev down
```

---

### Using the Shared VM Database (cs506x3a)

The backend and MySQL can also run on the course VM `cs506x3a.cs.wisc.edu`.

Open an SSH tunnel from your laptop:

   ```bash
   ssh -L 8080:localhost:8080 cslogin@cs506x3a.cs.wisc.edu
   ```

   Leave this session open.

All players are stored in the MySQL DB on `cs506x3a`, so everyone sees the same data.

---

### Python Client / Game
Set up a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

Run the game:

```bash
python src/main.py
```

### Testing

Run all JUnit tests:

```bash
gradle test
```

Check: build/reports for results
