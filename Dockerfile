# ---------- Stage 1: Build ----------
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app

RUN apt update && apt install -y findutils

# Copy Gradle wrapper and build files
COPY gradlew .
COPY gradle gradle
COPY build.gradle .
COPY settings.gradle .
COPY application.properties .
COPY application-test.properties .

# Copy source code
COPY src ./src

# Fix for Windows users
RUN apt-get update && apt-get install -y dos2unix \
   && dos2unix gradlew \
   && chmod +x gradlew

# Build the JAR (skip tests for faster builds)
RUN ./gradlew clean bootJar -x test

# ---------- Stage 2: Run ----------
FROM eclipse-temurin:21-jre
WORKDIR /app

# Fix for Windows users
RUN apt-get update && apt-get install -y dos2unix

# Copy built JAR from build stage
COPY --from=build /app/build/libs/*.jar app.jar

# Expose port
EXPOSE 8080

# Default: run the JAR
CMD ["java", "-jar", "app.jar"]
