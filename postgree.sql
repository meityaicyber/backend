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

CREATE TABLE IF NOT EXISTS "public"."vapt_reports" (
    "report_id"                     uuid            NOT NULL,
    "report_id_label"               varchar(100)    NOT NULL,
    "report_title"                  text,
    "report_type"                   varchar(100),
    "report_release_date"           date,
    "report_version"                varchar(20),
    "audit_type"                    varchar(100),
    "audit_period_from"             date,
    "audit_period_to"               date,
    "classification"                varchar(50),
    "document_title"                text,
    "document_version"              varchar(20),
    "prepared_by"                   varchar(150),
    "reviewed_by"                   varchar(150),
    "approved_by"                   varchar(150),
    "released_by"                   varchar(150),
    "release_date"                  date,
    "project_background"            text,
    "objective"                     text,
    "controlled_vocabulary_ref"     text,
    "total_findings"                integer         DEFAULT 0,
    "sev_critical"                  integer         DEFAULT 0,
    "sev_high"                      integer         DEFAULT 0,
    "sev_medium"                    integer         DEFAULT 0,
    "sev_low"                       integer         DEFAULT 0,
    "assessment_start_date"         date,
    "assessment_end_date"           date,
    "scope_updated_till"            date,
    "created_at"                    timestamptz     NOT NULL DEFAULT NOW(),
    "updated_at"                    timestamptz     NOT NULL DEFAULT NOW(),
    CONSTRAINT "vapt_reports_pkey"           PRIMARY KEY ("report_id"),
    CONSTRAINT "vapt_reports_report_id_fkey" FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_change_history" (
    "id"        uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id" uuid        NOT NULL,
    "version"   varchar(20),
    "date"      date,
    "remarks"   text,
    CONSTRAINT "vapt_change_history_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_change_history_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_distribution_list" (
    "id"            uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"     uuid        NOT NULL,
    "name"          varchar(150),
    "organization"  varchar(150),
    "designation"   varchar(150),
    "email"         varchar(150),
    CONSTRAINT "vapt_distribution_list_pkey"   PRIMARY KEY ("id"),
    CONSTRAINT "vapt_distribution_list_rep_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_assumptions" (
    "id"            uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"     uuid        NOT NULL,
    "sort_order"    integer,
    "assumption"    text,
    CONSTRAINT "vapt_assumptions_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_assumptions_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_assets" (
    "id"                 uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"          uuid        NOT NULL,
    "sr_no"              integer,
    "asset_description"  text,
    "url"                text,
    "criticality"        varchar(20),
    "internal_ip"        inet,
    "public_ip"          inet,
    "in_scope_functions" text,
    CONSTRAINT "vapt_assets_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_assets_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_exclusions" (
    "id"            uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"     uuid        NOT NULL,
    "sort_order"    integer,
    "exclusion"     text,
    CONSTRAINT "vapt_exclusions_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_exclusions_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_testing_credentials" (
    "id"        uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id" uuid        NOT NULL,
    "role"      varchar(100),
    "username"  varchar(150),
    "auth_type" varchar(100),
    "purpose"   text,
    CONSTRAINT "vapt_testing_credentials_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_testing_credentials_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_auditing_team" (
    "id"             uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"      uuid        NOT NULL,
    "user_id"        uuid,
    "sr_no"          integer,
    "name"           varchar(150),
    "designation"    varchar(150),
    "email"          varchar(150),
    "certifications" varchar(255),
    "cert_in_listed" boolean,
    CONSTRAINT "vapt_auditing_team_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_auditing_team_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE,
    CONSTRAINT "vapt_auditing_team_user_fk"   FOREIGN KEY (user_id)   REFERENCES users(user_id)          ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "public"."vapt_audit_activities" (
    "id"         uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"  uuid        NOT NULL,
    "date_label" varchar(100),
    "activity"   text,
    "outcome"    text,
    CONSTRAINT "vapt_audit_activities_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_audit_activities_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_standards" (
    "id"         uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"  uuid        NOT NULL,
    "sort_order" integer,
    "standard"   text,
    CONSTRAINT "vapt_standards_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_standards_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_methodology_phases" (
    "id"          uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"   uuid        NOT NULL,
    "phase"       varchar(50),
    "description" text,
    CONSTRAINT "vapt_methodology_phases_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_methodology_phases_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_tools" (
    "id"           uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"    uuid        NOT NULL,
    "sr_no"        integer,
    "tool_name"    varchar(150),
    "version"      varchar(50),
    "license_type" varchar(50),
    CONSTRAINT "vapt_tools_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_tools_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_findings" (
    "id"                      uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"               uuid        NOT NULL,
    "finding_id"              varchar(20) NOT NULL,
    "title"                   text,
    "severity"                varchar(20),
    "status"                  varchar(30),
    "new_or_repeat"           varchar(20),
    "cvss_score"              numeric(4,1),
    "cvss_vector"             varchar(100),
    "observation_description" text,
    "preconditions"           text,
    "impact"                  text,
    "likely_root_cause"       text,
    "recommendation"          text,
    "reference"               text,
    "retest_date"             date,
    "closure_evidence"        text,
    CONSTRAINT "vapt_findings_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_findings_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE,
    CONSTRAINT "vapt_findings_unique"    UNIQUE (report_id, finding_id)
);

CREATE TABLE IF NOT EXISTS "public"."vapt_finding_cwes" (
    "id"         uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"  uuid        NOT NULL,
    "finding_id" varchar(20) NOT NULL,
    "cwe"        varchar(30),
    CONSTRAINT "vapt_finding_cwes_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "vapt_finding_cwes_fk"   FOREIGN KEY (report_id, finding_id)
                                        REFERENCES vapt_findings(report_id, finding_id)
                                        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_finding_assets" (
    "id"         uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"  uuid        NOT NULL,
    "finding_id" varchar(20) NOT NULL,
    "asset_url"  text,
    CONSTRAINT "vapt_finding_assets_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "vapt_finding_assets_fk"   FOREIGN KEY (report_id, finding_id)
                                          REFERENCES vapt_findings(report_id, finding_id)
                                          ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_poc_steps" (
    "id"         uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"  uuid        NOT NULL,
    "finding_id" varchar(20) NOT NULL,
    "step_order" integer     NOT NULL,
    "step_text"  text,
    CONSTRAINT "vapt_poc_steps_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "vapt_poc_steps_fk"   FOREIGN KEY (report_id, finding_id)
                                     REFERENCES vapt_findings(report_id, finding_id)
                                     ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_risk_ratings" (
    "id"          uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id"   uuid        NOT NULL,
    "rating"      varchar(20),
    "description" text,
    CONSTRAINT "vapt_risk_ratings_pkey"       PRIMARY KEY ("id"),
    CONSTRAINT "vapt_risk_ratings_report_fk"  FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_remediation_roadmap" (
    "id"        uuid        NOT NULL DEFAULT gen_random_uuid(),
    "report_id" uuid        NOT NULL,
    "window"    varchar(50),
    "action"    text,
    CONSTRAINT "vapt_remediation_roadmap_pkey"      PRIMARY KEY ("id"),
    CONSTRAINT "vapt_remediation_roadmap_report_fk" FOREIGN KEY (report_id) REFERENCES vapt_reports(report_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."vapt_roadmap_findings" (
    "id"             uuid        NOT NULL DEFAULT gen_random_uuid(),
    "remediation_id" uuid        NOT NULL,
    "finding_id"     varchar(20),
    CONSTRAINT "vapt_roadmap_findings_pkey"   PRIMARY KEY ("id"),
    CONSTRAINT "vapt_roadmap_findings_rem_fk" FOREIGN KEY (remediation_id)
                                              REFERENCES vapt_remediation_roadmap(id)
                                              ON DELETE CASCADE
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

CREATE TABLE IF NOT EXISTS "public"."vulnerabilities" (
    "vuln_id"               uuid            NOT NULL DEFAULT gen_random_uuid(),
    "report_id"             uuid            NOT NULL,
    "vuln_seq_id"           smallint,
    "vulnerability_title"   text            NOT NULL,
    "category"              text,
    "severity"              severity_level,
    "cvss_score"            numeric(3,1)    CHECK (cvss_score BETWEEN 0.0 AND 10.0),
    "cve_ids"               text[],
    "cwe_ids"               text[],
    "affected_assets"       text[],
    "status"                vuln_status,
    "new_or_repeat"         text,
    "revalidation_status"   text,
    "detailed_observation"  text,
    "description"           text,
    "impact"                text,
    "recommendation"        text,
    "proof_of_concept"      text,
    "reproduction_steps"    text,
    "reference"             text,
    "meta"                  jsonb,
    "created_at"            timestamptz     NOT NULL DEFAULT now(),
    "updated_at"            timestamptz     NOT NULL DEFAULT now(),
    CONSTRAINT "vulnerabilities_pkey"      PRIMARY KEY ("vuln_id"),
    CONSTRAINT "vulnerabilities_report_fk" FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "idx_vulns_report_id"    ON "public"."vulnerabilities" ("report_id");
CREATE INDEX IF NOT EXISTS "idx_vulns_severity"     ON "public"."vulnerabilities" ("severity");
CREATE INDEX IF NOT EXISTS "idx_vulns_status"       ON "public"."vulnerabilities" ("status");
CREATE INDEX IF NOT EXISTS "idx_vulns_cve_ids"      ON "public"."vulnerabilities" USING GIN ("cve_ids");
CREATE INDEX IF NOT EXISTS "idx_vulns_cwe_ids"      ON "public"."vulnerabilities" USING GIN ("cwe_ids");
CREATE INDEX IF NOT EXISTS "idx_vulns_assets"       ON "public"."vulnerabilities" USING GIN ("affected_assets");
CREATE INDEX IF NOT EXISTS "idx_vulns_meta_gin"     ON "public"."vulnerabilities" USING GIN ("meta");