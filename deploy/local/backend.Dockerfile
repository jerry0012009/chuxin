FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY pom.xml ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.m2 mvn -B -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/target/chuxin-backend-*.jar app.jar
ENTRYPOINT ["sh", "-ec", "export JWT_SECRET=$(od -An -N32 -tx1 /dev/urandom | tr -d ' \\n'); exec java -Xms128m -Xmx640m -jar app.jar"]
