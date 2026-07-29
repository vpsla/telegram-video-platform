"""
Integration tests that require a real PostgreSQL instance.

These are skipped automatically when DATABASE_URL doesn't point to a
reachable Postgres server (e.g. local dev without Docker/Supabase, or
this sandbox) — they only actually run in CI, where the `postgres`
service container defined in .github/workflows/ci.yml is available.

Unlike the rest of the suite (which uses SQLite in-memory for speed),
these validate things SQLite can silently get wrong or simply doesn't
enforce: the full Alembic migration chain applying cleanly, ILIKE
case-insensitive search semantics, and BigInteger telegram_id storage.
"""
