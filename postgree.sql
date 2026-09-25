DROP TYPE IF EXISTS upload_status_enum CASCADE;

CREATE TYPE upload_status_enum AS ENUM (
    'pending',
    'validating',
    'processing',
    'completed',
    'failed',
    'quarantined'
);
CREATE TABLE IF NOT EXISTS "public"."agencies" (
    "agency_id"             uuid            NOT NULL,
    "created_at"            timestamptz     NOT NULL,
    "updated_at"            timestamptz     NOT NULL,
    "agency_code"           varchar(50)     NOT NULL,
    "agency_name"           varchar(255)    NOT NULL,
    "agency_type"           varchar(100)    NOT NULL,
    "registration_number"   varchar(100),
    "cert_in_empanelled"    boolean         NOT NULL,
    "empanelment_number"    varchar(100),
    "empanelment_expiry"    date,
    "contact_person"        varchar(255)    NOT NULL,
    "contact_email"         varchar(255)    NOT NULL,
    "contact_phone"         varchar(50),
    "website"               varchar(255),
    "address"               text,
    "city"                  varchar(100),
    "state"                 varchar(100),
    "country"               varchar(100)    NOT NULL,
    "pincode"               varchar(20),
    "status"                varchar(50)     NOT NULL,
    "onboarding_date"       date            NOT NULL,
    "remarks"               text,
    CONSTRAINT "agencies_pkey" PRIMARY KEY ("agency_id")
);

CREATE TABLE IF NOT EXISTS "public"."users" (
    "user_id"       uuid            NOT NULL,
    "username"      varchar(100)    NOT NULL,
    "email"         varchar(255)    NOT NULL,
    "password_hash" varchar(255)    NOT NULL,
    "full_name"     varchar(255),
    "is_active"     boolean         NOT NULL,
    "last_login"    timestamptz,
    "created_at"    timestamptz     NOT NULL,
    "updated_at"    timestamptz     NOT NULL,
    CONSTRAINT "users_pkey" PRIMARY KEY ("user_id")
);

CREATE TABLE IF NOT EXISTS "public"."roles" (
    "role_id"       serial          NOT NULL,
    "role_name"     varchar(50)     NOT NULL,
    "description"   text,
    CONSTRAINT "roles_pkey" PRIMARY KEY ("role_id")
);

CREATE TABLE IF NOT EXISTS "public"."user_roles" (
    "user_id"   uuid    NOT NULL,
    "role_id"   integer NOT NULL,
    CONSTRAINT "user_roles_pkey"        PRIMARY KEY ("user_id", "role_id"),
    CONSTRAINT "user_roles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT "user_roles_role_id_fkey" FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."user_sessions" (
    "session_id"            uuid            NOT NULL,
    "user_id"               uuid            NOT NULL,
    "refresh_token_hash"    varchar(255)    NOT NULL,
    "ip_address"            varchar(45),
    "user_agent"            text,
    "expires_at"            timestamptz     NOT NULL,
    "created_at"            timestamptz     NOT NULL,
    CONSTRAINT "user_sessions_pkey"         PRIMARY KEY ("session_id"),
    CONSTRAINT "user_sessions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."reports" (
    "report_id"         uuid                NOT NULL,
    "uploaded_by"       uuid,
    "agency_id"         uuid,
    "original_filename" varchar(500)        NOT NULL,
    "stored_filename"   varchar(500)        NOT NULL,
    "file_extension"    varchar(20)         NOT NULL,
    "mime_type"         varchar(100)        NOT NULL,
    "file_size"         bigint              NOT NULL,
    "sha256_hash"       varchar(64)         NOT NULL,
    "page_count"        integer,
    "upload_status"     upload_status_enum  NOT NULL,
    "simhash"           varchar(64),
    "created_at"        timestamptz         NOT NULL,
    "updated_at"        timestamptz         NOT NULL,
    CONSTRAINT "reports_pkey"                   PRIMARY KEY ("report_id"),
    CONSTRAINT "reports_uploaded_by_fkey"       FOREIGN KEY (uploaded_by) REFERENCES users(user_id)      ON DELETE SET NULL,
    CONSTRAINT "fk_reports_agency_id_agencies"  FOREIGN KEY (agency_id)   REFERENCES agencies(agency_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "public"."report_metadata" (
    "metadata_id"       uuid            NOT NULL,
    "report_id"         uuid            NOT NULL,
    "title"             varchar(500),
    "author"            varchar(255),
    "producer"          varchar(255),
    "subject"           text,
    "keywords"          text,
    "creation_date"     timestamptz,
    "modification_date" timestamptz,
    "metadata_json"     jsonb,
    "extracted_at"      timestamptz     NOT NULL,
    CONSTRAINT "report_metadata_pkey"           PRIMARY KEY ("metadata_id"),
    CONSTRAINT "report_metadata_report_id_fkey" FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."file_storage" (
    "storage_id"            uuid            NOT NULL,
    "report_id"             uuid            NOT NULL,
    "encrypted_file_path"   varchar(1000)   NOT NULL,
    "encryption_algorithm"  varchar(50),
    "encryption_key_id"     varchar(255),
    "checksum"              varchar(64),
    "stored_at"             timestamptz     NOT NULL,
    CONSTRAINT "file_storage_pkey"           PRIMARY KEY ("storage_id"),
    CONSTRAINT "file_storage_report_id_fkey" FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."file_validation" (
    "validation_id"         uuid            NOT NULL,
    "report_id"             uuid            NOT NULL,
    "file_type_valid"       boolean         NOT NULL,
    "malware_scan_status"   varchar(50)     NOT NULL,
    "duplicate_status"      varchar(50)     NOT NULL,
    "validation_status"     varchar(50)     NOT NULL,
    "validation_notes"      text,
    "validated_at"          timestamptz     NOT NULL,
    CONSTRAINT "file_validation_pkey"           PRIMARY KEY ("validation_id"),
    CONSTRAINT "file_validation_report_id_fkey" FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."partial_duplicates" (
    "duplicate_id"          uuid            NOT NULL,
    "report_id"             uuid            NOT NULL,
    "original_report_id"    uuid,
    "original_filename"     varchar(500),
    "hamming_distance"      integer,
    "detected_at"           timestamptz     NOT NULL,
    CONSTRAINT "partial_duplicates_pkey"                    PRIMARY KEY ("duplicate_id"),
    CONSTRAINT "partial_duplicates_report_id_fkey"          FOREIGN KEY (report_id)          REFERENCES reports(report_id) ON DELETE CASCADE,
    CONSTRAINT "partial_duplicates_original_report_id_fkey" FOREIGN KEY (original_report_id) REFERENCES reports(report_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "public"."audit_logs" (
    "log_id"        uuid            NOT NULL,
    "user_id"       uuid,
    "report_id"     uuid,
    "action"        varchar(100)    NOT NULL,
    "status"        varchar(50)     NOT NULL,
    "details"       jsonb,
    "created_at"    timestamptz     NOT NULL,
    CONSTRAINT "audit_logs_pkey"            PRIMARY KEY ("log_id"),
    CONSTRAINT "audit_logs_user_id_fkey"    FOREIGN KEY (user_id)   REFERENCES users(user_id)     ON DELETE SET NULL,
    CONSTRAINT "audit_logs_report_id_fkey"  FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "public"."security_events" (
    "event_id"          uuid            NOT NULL,
    "user_id"           uuid,
    "severity"          varchar(20)     NOT NULL,
    "event_type"        varchar(100)    NOT NULL,
    "description"       text,
    "created_at"        timestamptz     NOT NULL,
    "event_metadata"    jsonb,
    CONSTRAINT "security_events_pkey"           PRIMARY KEY ("event_id"),
    CONSTRAINT "security_events_user_id_fkey"   FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "public"."alembic_version" (
    "version_num" varchar(32) NOT NULL,
    CONSTRAINT "alembic_version_pkc" PRIMARY KEY ("version_num")
);



CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM ('Critical', 'High', 'Medium', 'Low', 'Informational');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE vuln_status AS ENUM ('Open', 'Closed', 'Accepted', 'Risk Accepted', 'In Progress');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS "public"."reports_data" (
    "report_id"         uuid            NOT NULL,
    "report_date"       date,
    "data"              jsonb           NOT NULL,
    "created_at"        timestamptz     NOT NULL DEFAULT now(),
    "updated_at"        timestamptz     NOT NULL DEFAULT now(),
    CONSTRAINT "reports_data_pkey"      PRIMARY KEY ("report_id"),
    CONSTRAINT "reports_data_report_fk" FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "idx_reports_report_date" ON "public"."reports_data" ("report_date");
CREATE INDEX IF NOT EXISTS "idx_reports_data_gin"    ON "public"."reports_data" USING GIN ("data");

DO $$ BEGIN
    CREATE TYPE observation_status AS ENUM ('Open', 'Closed', 'Partially Remediated');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE observation_severity AS ENUM ('Critical', 'High', 'Medium', 'Low');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE observation_impact AS ENUM ('Major', 'Moderate', 'Minor');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE observation_likelihood AS ENUM ('Easy', 'Moderate', 'Hard');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE observation_new_repeat AS ENUM ('New', 'Repeat');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS "public"."detailed_observations" (
    "finding_id"                uuid                    NOT NULL DEFAULT gen_random_uuid(),
    "report_id"                 uuid                    NOT NULL,
    "title"                     text,
    "status"                    observation_status,
    "severity"                  observation_severity,
    "impact_level"              observation_impact,
    "likelihood_level"          observation_likelihood,
    "cve_id"                    text[],         
    "cvss_score"                numeric(4,1),
    "cvss_vector"               text,
    "severity_rationale"        text,
    "reported_epss_score"       numeric(5,4),   
    "observation_date"          date,           
    "cwe"                       text[],         
    "affected_asset"            text[],         
    "regulatory_references"     text[],         
    "observation_description"   text,
    "preconditions"             text,
    "proof_of_concept"          jsonb,          
    "impact"                    text,
    "likely_root_cause"         text,
    "recommendation"            text,
    "reference"                 text,
    "new_or_repeat"             observation_new_repeat, 
    "meta"                      jsonb,
    "created_at"                timestamptz             NOT NULL DEFAULT now(),
    "updated_at"                timestamptz             NOT NULL DEFAULT now(),

    CONSTRAINT "detailed_observations_pkey"      PRIMARY KEY ("finding_id"),
    CONSTRAINT "detailed_observations_report_fk" FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "idx_obs_report_id" ON "public"."detailed_observations" ("report_id");
CREATE INDEX IF NOT EXISTS "idx_obs_severity"  ON "public"."detailed_observations" ("severity");
CREATE INDEX IF NOT EXISTS "idx_obs_status"    ON "public"."detailed_observations" ("status");
CREATE INDEX IF NOT EXISTS "idx_obs_meta_gin"  ON "public"."detailed_observations" USING GIN ("meta");