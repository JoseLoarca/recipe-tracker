# 0006: PostgreSQL + SQLAlchemy + Alembic

## Status
Accepted

## Context
The data model has real relational structure — users, households, memberships, recipes, ingredients, tags — with ownership and visibility rules that depend on joins across these tables.

## Decision
Use PostgreSQL as the datastore, SQLAlchemy as the ORM, and Alembic for schema migrations, rather than SQLite.

## Rationale
- Relational integrity (foreign keys, unique constraints like "one household per user") is easier to enforce correctly in Postgres than to hand-roll in SQLite for this schema.
- Runs as its own Docker Compose service with no meaningful added operational cost for a project that's already containerized.
- A visible, reviewable Alembic migration history is a stronger signal of engineering practice than a single schema-creation script, and matches how most production systems are actually built.
