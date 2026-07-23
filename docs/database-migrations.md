Model changes
    ↓
alembic revision --autogenerate -m "..."
    ↓
Review the migration
    ↓
alembic upgrade head
    ↓
alembic check
    ↓
Commit migration
    ↓
Open PR
    ↓
PR Check passes
    ↓
Merge
    ↓
Deploy