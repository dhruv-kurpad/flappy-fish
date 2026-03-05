# Troubleshooting Report

### System Specifications

**Operating System:** Windows

### Problem Description

Whenever I would run the command ```docker compose --profile dev up -d --build``` it wouldn't fully setup Spring Boot. After doing ```docker ps``` it just shows that the Spring Boot container is constantly restarting and never fully connecting.

### Problem Resolution

I added, with the help from copilot, 4 lines to the ```compose.yml``` file.
```SPRING_DATASOURCE_URL``` points Spring to the MySQL container hostname on the Docker network.
```SPRING_DATASOURCE_USERNAME``` and ```SPRING_DATASOURCE_PASSWORD``` provide credentials matching the MySQL service
```SPRING_DATASOURCE_DRIVER_CLASS_NAME``` ensures the MySQL driver is selected
```SPRING_JPA_HIBERNATE_DOL_AUTO=update``` lets Hibernate initialize/update schema so the app can fully boot

### Sources

- Copilot
- Postman AI assistant

