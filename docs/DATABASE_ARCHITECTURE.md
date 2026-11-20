# NEXORA AI - Database Architecture & Schema Blueprint

**Target Engine:** PostgreSQL 15+ (Production) | SQLite Async (Local Test Isolation)  
**ORM Framework:** SQLAlchemy 2.0 (Asyncio Engine)  
**Migration Tool:** Alembic  

---

## 1. Domain Entities & Relational Map

The central database is partitioned into 18 logical domains matching platform modules:

```
[ users ]
   │
   ├─► [ student_profiles ] ──► [ academic_records ]
   ├─► [ resumes ] ──► [ resume_sections ]
   ├─► [ assessment_attempts ] ──► [ attempt_answers ]
   ├─► [ coding_submissions ]
   ├─► [ interview_sessions ] ──► [ interview_messages ]
   ├─► [ study_plans ] ──► [ study_tasks ]
   ├─► [ flashcard_decks ] ──► [ flashcards ] ──► [ revision_reviews ]
   ├─► [ job_applications ]
   └─► [ audit_logs ]

[ companies ]
   ├─► [ placement_drives ] ──► [ drive_applications ]
   └─► [ questions ] ──► [ coding_problems ] & [ mcq_questions ]
```

---

## 2. Core Identity & RBAC Tables (Initial DDL Blueprint)

### Users Table (`users`):
- `id`: UUID (Primary Key)
- `email`: VARCHAR(255) (Unique, Indexed)
- `hashed_password`: VARCHAR(255)
- `role`: ENUM (`STUDENT`, `ADMIN`, `PLACEMENT_CELL`)
- `is_active`: BOOLEAN (Default True)
- `is_verified`: BOOLEAN (Default False)
- `created_at`: TIMESTAMP WITH TIME ZONE
- `updated_at`: TIMESTAMP WITH TIME ZONE

### Student Profiles (`student_profiles`):
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> `users.id`, Unique, Indexed)
- `full_name`: VARCHAR(255)
- `department`: VARCHAR(100)
- `batch_year`: INTEGER
- `cgpa`: NUMERIC(4, 2)
- `readiness_score`: INTEGER (0-100)
- `github_username`: VARCHAR(100)
- `linkedin_url`: VARCHAR(255)

---

## 3. Storage, Indexing & Backup Policy

- **Primary Keys:** UUIDv4 across all public-facing entities to eliminate sequential enumeration attacks.
- **Foreign Keys:** Strictly enforced with `ON DELETE CASCADE` or `RESTRICT` depending on domain safety rules.
- **Indices:** Composite B-tree indices on `(user_id, created_at)` for paginated user activity feeds.
- **Backup Procedures:** Daily split gzip dumps (< 1 GB per chunk) compatible with FAT32 storage constraints.
