-- ==============================================================================
-- NEXORA AI — PostgreSQL 17 Staged Provisioning Runbook (pgAdmin 4 GUI Query Tool)
-- Target Databases: nexora_dev, nexora_test
-- Target Role: nexora_app (Least Privilege)
-- ==============================================================================
-- MANDATORY EXECUTION INSTRUCTIONS:
-- 1. THIS RUNBOOK CANNOT BE EXECUTED AS A SINGLE CONTINUOUS SCRIPT.
--    PostgreSQL strictly prohibits 'CREATE DATABASE' inside transaction blocks or
--    multi-statement scripts executed in a single transaction context.
-- 2. ZERO PASSWORDS ARE STORED IN THIS FILE. Follow Phase 2 for secure GUI password setting.
-- 3. Execute each Phase sequentially in the exact database connection context specified.
-- 4. PREFLIGHT SAFETY GATE: If any check in Phase 1 reports unexpected memberships
--    or existing databases, STOP IMMEDIATELY and do not proceed.
-- ==============================================================================

-- ==============================================================================
-- PHASE 1: PREFLIGHT AUDIT & LEAST-PRIVILEGE ROLE ENFORCEMENT
-- Connection Context: Connect pgAdmin Query Tool to server default database ('postgres')
-- ==============================================================================

-- Step 1A: Check for unexpected direct and indirect (nested) memberships for nexora_app
-- Note on NOINHERIT vs SET ROLE:
-- NOINHERIT prevents nexora_app from automatically inheriting group privileges.
-- However, if nexora_app is granted membership in an elevated role (directly or via nested role chains),
-- a session can explicitly execute 'SET ROLE' to elevate privileges.
-- Inspect the result below: if rows are returned with unexpected roles, STOP!
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

-- Step 1B: Check target database existence and ownership before creation
-- STRICT SAFETY INVARIANT:
-- If nexora_dev or nexora_test ALREADY EXISTS (regardless of owner, including CURRENT_USER),
-- DO NOT PROCEED with automatic provisioning!
-- Pre-existing databases might be used by another system, and altering ownership or
-- revoking PUBLIC permissions could disrupt live workflows.
SELECT 
   d.datname AS database_name, 
   pg_catalog.pg_get_userbyid(d.datdba) AS current_owner,
   d.encoding,
   d.datcollate
FROM pg_catalog.pg_database d 
WHERE d.datname IN ('nexora_dev', 'nexora_test');

-- Step 1C: Enforce least-privilege attributes on nexora_app
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
-- PHASE 2: INITIAL PASSWORD SETTING & ROTATION SAFETY
-- ==============================================================================
-- SAFETY NOTICE:
-- To prevent accidental application downtime, do NOT change the password if nexora_app
-- already has an active password in use by the running backend.
--
-- INITIAL SETUP PROCEDURE (First-Time Only):
-- 1. In pgAdmin left object tree, expand 'Login/Group Roles'.
-- 2. Right-click 'nexora_app' -> Select 'Properties...'.
-- 3. Navigate to the 'Definition' tab.
-- 4. Enter your chosen strong password in the 'Password' field.
-- 5. Click 'Save'.
--
-- INTENTIONAL PASSWORD ROTATION PROCEDURE:
-- When intentionally rotating credentials:
-- 1. Perform Steps 1-5 above to update the role password in PostgreSQL.
-- 2. URL-encode any special characters in the new password (e.g., '@' -> '%40').
-- 3. Update 'DATABASE_URL' and 'TEST_DATABASE_URL' in backend/.env immediately.
-- 4. Restart backend services to re-establish the connection pool.

-- ==============================================================================
-- PHASE 3: DISCRETE DATABASE CREATION
-- Connection Context: Query Tool on 'postgres' database (Ensure 'Auto-commit' is ON)
-- ==============================================================================
-- INSTRUCTIONS:
-- Execute Statement 3A and 3B individually.
-- If Step 1B returned rows showing that either database already exists,
-- DO NOT execute that CREATE statement. Follow docs/POSTGRESQL_FINAL_EXECUTION_RUNBOOK.md.

-- Step 3A: Create nexora_dev (Highlight and execute ONLY if nexora_dev does not exist)
CREATE DATABASE nexora_dev OWNER nexora_app ENCODING 'UTF8';

-- Step 3B: Create nexora_test (Highlight and execute ONLY if nexora_test does not exist)
CREATE DATABASE nexora_test OWNER nexora_app ENCODING 'UTF8';

-- ==============================================================================
-- PHASE 4: CONFIGURE PERMISSIONS ON NEWLY CREATED nexora_dev
-- Connection Context: Open a NEW Query Tool connected directly to 'nexora_dev'
-- ==============================================================================
-- STOP CHECK: Verify that nexora_dev was newly created and is owned by nexora_app before running Phase 4!
-- NEVER run these statements on pre-existing databases.

-- Revoke broad public schema permissions on dedicated NEXORA database
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
-- PHASE 5: CONFIGURE PERMISSIONS ON NEWLY CREATED nexora_test
-- Connection Context: Open a NEW Query Tool connected directly to 'nexora_test'
-- ==============================================================================
-- STOP CHECK: Verify that nexora_test was newly created and is owned by nexora_app before running Phase 5!
-- NEVER run these statements on pre-existing databases.

-- Revoke broad public schema permissions on dedicated NEXORA test database
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
-- PHASE 6: FINAL VERIFICATION AUDIT QUERIES
-- Connection Context: Query Tool on 'postgres' or 'nexora_dev'
-- ==============================================================================

-- 6A: Verify Role Attributes (All false except rolcanlogin = true)
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

-- 6B: Verify Database Ownership (Must show owner_name = nexora_app)
SELECT 
   datname AS database_name, 
   pg_catalog.pg_get_userbyid(datdba) AS owner_name, 
   encoding, 
   datcollate 
FROM pg_database 
WHERE datname IN ('nexora_dev', 'nexora_test');

-- 6C: Verify Schema Privileges (Execute inside nexora_dev and nexora_test)
SELECT 
   nspname AS schema_name, 
   has_schema_privilege('nexora_app', nspname, 'USAGE') AS has_usage,
   has_schema_privilege('nexora_app', nspname, 'CREATE') AS has_create
FROM pg_namespace 
WHERE nspname = 'public';
