-- Creates one database per service, mirroring the "database-per-service"
-- pattern in the Optum UM architecture (each service owns its store).
-- Runs once, on the first boot of the postgres volume.

CREATE DATABASE um_case;
CREATE DATABASE um_intake;
CREATE DATABASE camunda;

-- Room to grow into the other services from the diagram later:
-- CREATE DATABASE member;
-- CREATE DATABASE provider;
-- CREATE DATABASE configuration;
-- CREATE DATABASE reference_data;

-- All owned by the umlite role created via POSTGRES_USER.
GRANT ALL PRIVILEGES ON DATABASE um_case   TO umlite;
GRANT ALL PRIVILEGES ON DATABASE um_intake TO umlite;
GRANT ALL PRIVILEGES ON DATABASE camunda   TO umlite;
