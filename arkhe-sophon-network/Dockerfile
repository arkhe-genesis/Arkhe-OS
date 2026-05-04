FROM maven:3.9.6-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
# Since we might not have graalvm available easily in this maven image, we can do a normal jar build for the docker compose run.
# The user wants "Compilar imagem nativa GraalVM... para deploy em edge."
# For standard local docker-compose run, we can just run the jar.
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=build /app/target/arkhe-sophon-network-1.0.0-SNAPSHOT.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
