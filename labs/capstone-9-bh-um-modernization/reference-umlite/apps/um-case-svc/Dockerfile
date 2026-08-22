# Multi-stage build for the Spring Boot case service (Phase 6 / Track 6, M30).
# Stage 1 builds the jar with Maven; stage 2 ships only a JRE + the jar → small, no build tools at runtime.

# --- build stage ---
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
# Cache dependencies first: copy the wrapper + pom, resolve, then copy sources.
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN ./mvnw -q -B dependency:go-offline
COPY src/ src/
RUN ./mvnw -q -B -DskipTests package

# --- runtime stage ---
FROM eclipse-temurin:21-jre AS runtime
WORKDIR /app
# Run as a non-root user.
RUN useradd -r -u 1001 spring
USER spring
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
