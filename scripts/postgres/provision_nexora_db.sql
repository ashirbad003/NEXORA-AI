-- ==============================================================================
-- NEXORA AI — PostgreSQL 17 Least-Privilege Provisioning Script
-- Target Databases: nexora_dev, nexora_test
-- Target Role: nexora_app (Least Privilege)
-- Compatible with: psql interactive CLI (PostgreSQL 14, 15, 16, 17)
-- ==============================================================================
-- STRICT SAFETY INVARIANTS:
-- 1. ERROR-STOP: ON_ERROR_STOP is enabled. Any failure immediately stops execution.
-- 2. EXISTING DATABASE PROTECTION: If either nexora_dev or nexora_test ALREADY EXISTS
--    before this script runs, provisioning STOPS immediately. It will NEVER modify,
--    recreate, reassign ownership, or revoke public permissions on existing databases.
-- 3. PASSWORD PRESERVATION: Routine provisioning NEVER prompts for or alters passwords.
--    Initial password setup and intentional password rotation are strictly separated
--    into standalone, administrator-controlled procedures.
-- 4. LEAST PRIVILEGE: Enforces LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
--    NOINHERIT NOREPLICATION NOBYPASSRLS.
-- 5. MEMBERSHIP AUDIT: Halts immediately if unexpected role memberships are detected.
-- ==============================================================================

-- Enable strict error handling: abort on any command or SQL failure
\set ON_ERROR_STOP on

\echo '------------------------------------------------------------'
\echo 'NEXORA AI: PostgreSQL 17 Safe Least-Privilege Provisioning'
\echo '------------------------------------------------------------'

-- ==============================================================================
-- STEP 1: PREFLIGHT AUDIT — EXISTING ROLE MEMBERSHIPS & UNEXPECTED PRIVILEGES
-- ==============================================================================
-- Documenting NOINHERIT vs SET ROLE & Recursive / Inherited Memberships:
-- NOINHERIT prevents nexora_app from automatically inheriting privileges of group roles.
-- However, if nexora_app is granted membership (directly or via nested role chains) in an
-- elevated role (e.g. pg_read_all_data, pg_database_owner, or a superuser group), a connected
-- session could explicitly invoke 'SET ROLE <elevated_role>' and acquire higher privileges.
-- Therefore, any unexpected role membership (direct or indirect) must trigger a safety stop.

DO
$do$
DECLARE
   unexpected_memberships TEXT;
BEGIN
   -- Check direct and indirect (recursive) role memberships using WITH RECURSIVE
   WITH RECURSIVE member_tree AS (
      -- Direct memberships
      SELECT am.roleid, am.member, am.admin_option
      FROM pg_auth_members am
      JOIN pg_roles r ON r.oid = am.member
      WHERE r.rolname = 'nexora_app'
      UNION
      -- Recursive (indirect/nested) memberships
      SELECT am.roleid, am.member, am.admin_option
      FROM pg_auth_members am
      JOIN member_tree mt ON am.member = mt.roleid
   )
   SELECT string_agg(m.rolname, ', ')
   INTO unexpected_memberships
   FROM member_tree mt
   JOIN pg_roles m ON mt.roleid = m.oid;

   IF unexpected_memberships IS NOT NULL THEN
      RAISE EXCEPTION 'SAFETY STOP: Role nexora_app has direct or indirect membership in: [%]. Elevated or unexpected role memberships could allow unintended privilege escalation via SET ROLE. Provisioning halted. Review and resolve role memberships manually before proceeding.', unexpected_memberships;
   END IF;
END
$do$;

-- Display direct and nested membership status (reporting admin_option accurately)
WITH RECURSIVE member_tree AS (
   SELECT am.roleid, am.member, am.admin_option, 1 AS depth
   FROM pg_auth_members am
   JOIN pg_roles r ON r.oid = am.member
   WHERE r.rolname = 'nexora_app'
   UNION
   SELECT am.roleid, am.member, am.admin_option, mt.depth + 1
   FROM pg_auth_members am
   JOIN member_tree mt ON am.member = mt.roleid
)
SELECT 
   'nexora_app' AS target_role,
   m.rolname AS member_of_role,
   mt.admin_option,
   mt.depth AS inheritance_depth
FROM member_tree mt
JOIN pg_roles m ON mt.roleid = m.oid;

-- ==============================================================================
-- STEP 2: PREFLIGHT AUDIT — STRICT EXISTING DATABASE PROTECTION
-- ==============================================================================
-- Strict Safety Rule: If nexora_dev or nexora_test already exists (regardless of
-- who owns it, including CURRENT_USER), provisioning MUST STOP.
-- Pre-existing databases might be shared with other services or managed externally.
-- Automatic provisioning is strictly restricted to greenfield creation of new databases.

DO
$do$
DECLARE
   existing_dbs TEXT;
BEGIN
   SELECT string_agg(d.datname || ' (owner: ' || pg_catalog.pg_get_userbyid(d.datdba) || ')', ', ')
   INTO existing_dbs
   FROM pg_catalog.pg_database d
   WHERE d.datname IN ('nexora_dev', 'nexora_test');

   IF existing_dbs IS NOT NULL THEN
      RAISE EXCEPTION 'SAFETY STOP: Target database(s) already exist: [%]. Automatic provisioning is prohibited against existing databases to prevent breaking permissions, ownership, or co-located applications. If these databases are intended for NEXORA AI, follow the manual inspection runbook in docs/POSTGRESQL_FINAL_EXECUTION_RUNBOOK.md.', existing_dbs;
   END IF;
END
$do$;

-- ==============================================================================
-- STEP 3: IDEMPOTENT ROLE CREATION WITH STRICT LEAST PRIVILEGE
-- ==============================================================================
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'nexora_app') THEN
      CREATE ROLE nexora_app WITH 
         LOGIN 
         NOSUPERUSER 
         NOCREATEDB 
         NOCREATEROLE 
         NOINHERIT 
         NOREPLICATION 
         NOBYPASSRLS;
      RAISE NOTICE 'Role nexora_app created with strict least-privilege attributes.';
   ELSE
      RAISE NOTICE 'Role nexora_app already exists. Enforcing least-privilege attributes.';
      ALTER ROLE nexora_app WITH 
         LOGIN 
         NOSUPERUSER 
         NOCREATEDB 
         NOCREATEROLE 
         NOINHERIT 
         NOREPLICATION 
         NOBYPASSRLS;
   END IF;
END
$do$;

-- ==============================================================================
-- STEP 4: PASSWORD STATUS AUDIT (ZERO PASSWORD ALTERATION IN ROUTINE SCRIPT)
-- ==============================================================================
-- Policy: This script NEVER prompts for or alters passwords during routine runs.
-- If the role is newly created and has no password, a notification is output.
-- The administrator sets or rotates passwords outside this script via:
--   \password nexora_app
-- This guarantees zero accidental password resets and zero credential exposure.

DO
$do$
DECLARE
   has_verifier BOOLEAN;
BEGIN
   -- Check if a password verifier is set in pg_shadow or pg_authid.
   -- In PostgreSQL, pg_shadow is accessible to superusers and reports passwd IS NOT NULL.
   -- If current_user has insufficient privileges to query pg_shadow, fallback safely.
   BEGIN
      SELECT (passwd IS NOT NULL) INTO has_verifier
      FROM pg_shadow WHERE usename = 'nexora_app';
   EXCEPTION WHEN insufficient_privilege THEN
      has_verifier := NULL;
   END;

   IF has_verifier IS FALSE THEN
      RAISE NOTICE '>>> ATTENTION: Role nexora_app currently has NO password set.';
      RAISE NOTICE '>>> After this script completes, run "\password nexora_app" in psql to set credentials.';
   ELSIF has_verifier IS TRUE THEN
      RAISE NOTICE '>>> Role nexora_app has an active password verifier. Existing credentials preserved untouched.';
   ELSE
      RAISE NOTICE '>>> Note: Password verifier status could not be read directly. Existing credentials will remain untouched.';
   END IF;
END
$do$;

-- ==============================================================================
-- STEP 5: SAFE DATABASE CREATION OUTSIDE TRANSACTION BLOCK
-- ==============================================================================
-- Notice: CREATE DATABASE cannot execute inside a transaction block.
-- The query below generates 'CREATE DATABASE ...' using \gexec.
-- Because Step 2 verified neither database exists, these statements execute cleanly.
SELECT 'CREATE DATABASE nexora_dev OWNER nexora_app ENCODING ''UTF8'''\gexec

SELECT 'CREATE DATABASE nexora_test OWNER nexora_app ENCODING ''UTF8'''\gexec

-- ==============================================================================
-- STEP 6: CONFIGURE PERMISSIONS ON NEWLY CREATED nexora_dev
-- ==============================================================================
\connect nexora_dev

-- Revoke broad public schema permissions on this newly created database
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Grant required database-level access
GRANT CONNECT, TEMPORARY ON DATABASE nexora_dev TO nexora_app;

-- Grant required schema-level access for Alembic DDL & runtime operations
GRANT USAGE, CREATE ON SCHEMA public TO nexora_app;

-- Configure default privileges for future objects created by nexora_app
ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public 
   GRANT ALL ON TABLES TO nexora_app;
ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public 
   GRANT ALL ON SEQUENCES TO nexora_app;

-- Configure default privileges for future objects created by administrator / current role
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
   GRANT ALL ON TABLES TO nexora_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
   GRANT ALL ON SEQUENCES TO nexora_app;

-- ==============================================================================
-- STEP 7: CONFIGURE PERMISSIONS ON NEWLY CREATED nexora_test
-- ==============================================================================
\connect nexora_test

-- Revoke broad public schema permissions on this newly created test database
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Grant required database-level access
GRANT CONNECT, TEMPORARY ON DATABASE nexora_test TO nexora_app;

-- Grant required schema-level access for Alembic DDL & runtime operations
GRANT USAGE, CREATE ON SCHEMA public TO nexora_app;

-- Configure default privileges for future objects created by nexora_app
ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public 
   GRANT ALL ON TABLES TO nexora_app;
ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public 
   GRANT ALL ON SEQUENCES TO nexora_app;

-- Configure default privileges for future objects created by administrator / current role
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
   GRANT ALL ON TABLES TO nexora_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
   GRANT ALL ON SEQUENCES TO nexora_app;

-- ==============================================================================
-- STEP 8: POST-PROVISIONING VERIFICATION AUDIT
-- ==============================================================================
\echo '------------------------------------------------------------'
\echo 'Verification 1: Role Attributes for nexora_app'
\echo '------------------------------------------------------------'
SELECT 
   rolname, 
   rolsuper AS is_superuser, 
   rolinherit AS inherits_privileges, 
   rolcreaterole AS can_create_roles, 
   rolcreatedb AS can_create_db, 
   rolcanlogin AS can_login, 
   rolreplication AS is_replication, 
   rolbypassrls AS bypasses_rls
FROM pg_roles 
WHERE rolname = 'nexora_app';

\echo '------------------------------------------------------------'
\echo 'Verification 2: Database Ownership'
\echo '------------------------------------------------------------'
SELECT d.datname AS database_name, pg_catalog.pg_get_userbyid(d.datdba) AS owner_name
FROM pg_database d WHERE d.datname IN ('nexora_dev', 'nexora_test');

\echo '------------------------------------------------------------'
\echo 'Verification 3: Public Schema Privileges (inside nexora_test)'
\echo '------------------------------------------------------------'
SELECT 
   nspname AS schema_name, 
   has_schema_privilege('nexora_app', nspname, 'USAGE') AS has_usage,
   has_schema_privilege('nexora_app', nspname, 'CREATE') AS has_create
FROM pg_namespace 
WHERE nspname = 'public';

\echo '------------------------------------------------------------'
\echo 'Provisioning complete. If nexora_app has no password set,'
\echo 'execute "\password nexora_app" now.'
\echo '------------------------------------------------------------'
