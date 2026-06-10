# Build stage: use Gradle image
FROM gradle:8-jdk21 AS builder
WORKDIR /app

COPY build.gradle .
COPY settings.gradle .
COPY src src
RUN gradle bootJar --no-daemon

# Run stage: only the JAR and runtime
FROM eclipse-temurin:21-jdk-jammy
WORKDIR /app
COPY --from=builder /app/build/libs/*-SNAPSHOT.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
