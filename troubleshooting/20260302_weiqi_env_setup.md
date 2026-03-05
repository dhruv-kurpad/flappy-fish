# Troubleshooting Report - Sprint 1 Integration



**System Specifications**

* **Operating System:** macOS (Apple Silicon / arm64)



**Problem Description**

1. **Frontend Dependency:** The Python CLI failed with `ModuleNotFoundError: No module named 'requests'`.

2. **Connection Refused:** Teammates could not connect to the Spring Boot backend at `localhost:8080`, receiving "Unable to connect" errors.

3. **Environment Inconsistency:** Running via `./gradlew bootRun` failed on some machines due to missing `gradle-wrapper.jar` or local Java version issues.



**Problem Resolution**

1. **Dependency Fix:** Installed missing HTTP libraries using `pip3 install requests`.

2. **Core Solution (Docker Orchestration):** Standardized the team’s environment by using the command:

`docker compose --profile dev up -d --build`

This ensured that the Spring Boot app and MySQL were built inside containers with a pre-configured network, bypassing local environment blockers.

3. **Verification:** Confirmed success via Postman (200 OK) and successfully logged into the "weiqi" account through the Python CLI.



**Sources**

* "Used Gemini to troubleshoot the environment setup and verify the API integration flow."

* Analyzed team terminal logs and error reports (Joeprei20) to identify cross-platform connectivity issues.