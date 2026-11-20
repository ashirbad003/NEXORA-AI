import asyncio
from pathlib import Path
from dotenv import dotenv_values
import asyncpg

env_path = Path('backend/.env')
env_dict = dotenv_values(env_path)
url_dev = env_dict.get('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
url_test = env_dict.get('TEST_DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')

async def inspect():
    print("=== NEXORA_DEV READ-ONLY INSPECTION ===")
    conn_dev = await asyncpg.connect(url_dev)
    current_db = await conn_dev.fetchval("SELECT current_database();")
    current_user = await conn_dev.fetchval("SELECT current_user;")
    print(f"Connected Database: {current_db}")
    print(f"Connected User: {current_user}")
    
    alembic_head = await conn_dev.fetchval("SELECT version_num FROM alembic_version;")
    print(f"Alembic Version: {alembic_head}")
    
    tables = await conn_dev.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    print(f"Tables Count: {len(tables)}")
    for r in tables:
        t = r['table_name']
        cnt = await conn_dev.fetchval(f'SELECT COUNT(*) FROM "{t}";')
        print(f"  - {t}: {cnt} rows")
        
    indexes = await conn_dev.fetch("""
        SELECT tablename, indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        ORDER BY tablename, indexname;
    """)
    print(f"Total Indexes: {len(indexes)}")
    for idx in indexes:
        print(f"  - {idx['tablename']}.{idx['indexname']}")
        
    fks = await conn_dev.fetch("""
        SELECT conname, conrelid::regclass AS table_from, confrelid::regclass AS table_to
        FROM pg_constraint
        WHERE contype = 'f' AND connamespace = 'public'::regnamespace
        ORDER BY conname;
    """)
    print(f"Total Foreign Keys: {len(fks)}")
    for fk in fks:
        print(f"  - {fk['conname']}: {fk['table_from']} -> {fk['table_to']}")

    await conn_dev.close()
    
    print("\n=== NEXORA_TEST READ-ONLY INSPECTION ===")
    conn_test = await asyncpg.connect(url_test)
    test_db = await conn_test.fetchval("SELECT current_database();")
    test_user = await conn_test.fetchval("SELECT current_user;")
    print(f"Connected Database: {test_db}")
    print(f"Connected User: {test_user}")
    test_tables = await conn_test.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    print(f"Tables Count in nexora_test: {len(test_tables)}")
    for r in test_tables:
        t = r['table_name']
        cnt = await conn_test.fetchval(f'SELECT COUNT(*) FROM "{t}";')
        print(f"  - {t}: {cnt} rows")
    await conn_test.close()

if __name__ == "__main__":
    asyncio.run(inspect())
