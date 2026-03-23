FROM gitlab/gitlab-runner:v16.4.0

RUN apt-get update && \
    apt-get install -y software-properties-common curl && \
    apt-get install -y git openjdk-21-jdk dos2unix
RUN git config --global --add safe.directory /app/.git || echo "not needed"
RUN git config --global --add safe.directory /app || echo "not needed"

COPY ./gradlew /app/gradlew
COPY ./gradle /app/gradle
COPY ./settings.gradle /app/settings.gradle
COPY ./build.gradle /app/build.gradle

WORKDIR /app

RUN dos2unix ./gradlew && chmod +x ./gradlew && ./gradlew --no-daemon dependencies

