-- ==============================================================================
-- NEXORA AI — Read-Only Forensic Audit Queries for Existing Databases
-- Targets: nexora_dev, nexora_test, role nexora_app
-- STRICTLY READ-ONLY: ZERO MODIFICATIONS, ZERO WRITES, ZERO DROPS
-- ==============================================================================

-- 1. Database Identification, Ownership, Encoding and Collation
SELECT 
    d.datname AS database_name,
    pg_catalog.pg_get_userbyid(d.datdba) AS owner_name,
    pg_catalog.pg_encoding_to_char(d.encoding) AS encoding,
    d.datcollate AS collation,
    d.datctype AS ctype,
    pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) AS db_size
FROM pg_catalog.pg_database d
WHERE d.datname IN ('nexora_dev', 'nexora_test', 'postgres')
ORDER BY d.datname;

-- 2. Role Attributes and Privilege Flags for nexora_app
SELECT 
    r.rolname,
    r.rolsuper AS is_superuser,
    r.rolinherit AS inherits_privileges,
    r.rolcreaterole AS can_create_roles,
    r.rolcreatedb AS can_create_db,
    r.rolcanlogin AS can_login,
    r.rolreplication AS is_replication,
    r.rolbypassrls AS bypasses_rls,
    r.rolconnlimit AS conn_limit,
    r.rolvaliduntil AS valid_until
FROM pg_catalog.pg_roles r
WHERE r.rolname IN ('nexora_app', 'postgres');

-- 3. Recursive Role Membership Audit (Direct and Indirect/Inherited)
WITH RECURSIVE member_tree AS (
    SELECT am.roleid, am.member, am.admin_option, 1 AS depth
    FROM pg_catalog.pg_auth_members am
    JOIN pg_catalog.pg_roles r ON r.oid = am.member
    WHERE r.rolname = 'nexora_app'
    UNION
    SELECT am.roleid, am.member, am.admin_option, mt.depth + 1
    FROM pg_catalog.pg_auth_members am
    JOIN member_tree mt ON am.member = mt.roleid
)
SELECT 
    'nexora_app' AS target_role,
    m.rolname AS member_of_role,
    mt.admin_option,
    mt.depth AS inheritance_depth
FROM member_tree mt
JOIN pg_catalog.pg_roles m ON mt.roleid = m.oid;

-- 4. Connection Privileges on nexora_dev and nexora_test
SELECT 
    d.datname AS database_name,
    has_database_privilege('nexora_app', d.datname, 'CONNECT') AS has_connect,
    has_database_privilege('nexora_app', d.datname, 'TEMPORARY') AS has_temporary,
    has_database_privilege('nexora_app', d.datname, 'CREATE') AS has_create
FROM pg_catalog.pg_database d
WHERE d.datname IN ('nexora_dev', 'nexora_test');

-- 5. Existing Installed Extensions in Current Database
SELECT 
    extname,
    extversion
FROM pg_catalog.pg_extension;

-- 6. Existing Schemas in Current Database
SELECT 
    nspname AS schema_name,
    pg_catalog.pg_get_userbyid(nspowner) AS schema_owner,
    has_schema_privilege('nexora_app', nspname, 'USAGE') AS nexora_app_usage,
    has_schema_privilege('nexora_app', nspname, 'CREATE') AS nexora_app_create
FROM pg_catalog.pg_namespace
WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema';

-- 7. Existing Tables, Row Counts, and Sizes in public Schema
SELECT 
    t.table_schema,
    t.table_name,
    t.table_type,
    pg_catalog.pg_size_pretty(pg_catalog.pg_total_relation_size(quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))) AS total_size
FROM information_schema.tables t
WHERE t.table_schema = 'public'
ORDER BY t.table_name;

-- 8. Alembic Version Table Check (Migration History)
SELECT * FROM alembic_version;
