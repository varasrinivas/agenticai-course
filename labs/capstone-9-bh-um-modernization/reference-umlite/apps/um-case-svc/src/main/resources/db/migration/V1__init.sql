-- Schema for the Prior Auth case. Owned by um-case-svc, managed by Flyway.
CREATE TABLE prior_auth_case (
    id              UUID PRIMARY KEY,
    member_id       VARCHAR(32)  NOT NULL,
    provider_id     VARCHAR(32)  NOT NULL,
    procedure_code  VARCHAR(10)  NOT NULL,
    diagnosis_code  VARCHAR(10)  NOT NULL,
    requested_units INTEGER      NOT NULL,
    status          VARCHAR(16)  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL,
    updated_at      TIMESTAMPTZ  NOT NULL
);

CREATE INDEX idx_pac_member ON prior_auth_case (member_id);
CREATE INDEX idx_pac_status ON prior_auth_case (status);
