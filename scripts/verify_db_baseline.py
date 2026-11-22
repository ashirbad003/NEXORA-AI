import asyncio, asyncpg, os
from dotenv import load_dotenv

load_dotenv('backend/.env')
db_url = os.environ.get('DATABASE_URL')
user_pass_host = db_url.split('://')[1]
auth_part, host_db = user_pass_host.split('@')
user, password = auth_part.split(':')
host_port, dbname = host_db.split('/')
host, port = host_port.split(':')

async def main():
    conn = await asyncpg.connect(user=user, password=password, host=host, port=port, database=dbname)
    baseline_ids = [
        '5bd31e4b-2c8f-43b3-a2bf-c585637ff7bf',
        '4479063d-f5ea-4c75-90e7-96849ec71107',
        'test-student-p8-1795273011',
        'test-student-p8-1795273012',
        'test-p8-c39f84fa-b20',
        'test-p8-fb400e8d-6e9',
        'test-p8-3d679cf4-4c9'
    ]
    formatted = ", ".join("'" + x + "'" for x in baseline_ids)
    query = "SELECT id, email, full_name, hashed_password, is_active FROM users WHERE id IN (" + formatted + ") ORDER BY id;"
    rows = await conn.fetch(query)
    print("Matching baseline users in " + dbname + ": " + str(len(rows)) + "/7")
    for r in rows:
        print("  ID: " + str(r['id']) + " | Email: " + str(r['email']) + " | Name: " + str(r['full_name']) + " | Hash: " + str(r['hashed_password']))
    
    total = await conn.fetchval("SELECT count(*) FROM users;")
    print("Total users in " + dbname + ": " + str(total))

    audit = await conn.fetchrow("SELECT id, email, is_active FROM users WHERE email = 'nexora.audit@example.com'")
    if audit:
        print("Audit user: " + str(audit['id']) + " | " + str(audit['email']) + " | " + str(audit['is_active']))

    await conn.close()

asyncio.run(main())
