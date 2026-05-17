# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0] - 2026-05-16

### Added

- OrgUnit self-referencing tree with full CRUD (POST, PATCH, GET, GET /tree, GET /history)
- Person flat table with full CRUD (POST, PATCH, GET, GET /history)
- Assignment bridge table linking OrgUnit and Person (POST, PATCH, GET, GET /history)
- Open position support: assignment can be created without a person (person_id nullable)
- Fill / vacate assignment via PATCH person_id
- Bi-temporal data model: valid_from / valid_until (sentinel 9999-12-31) + updated_at
- mutation_reason mandatory on every POST and PATCH (HTTP 422 if missing)
- History tables for all 3 entities: org_unit_history, person_history, assignment_history
- Every PATCH copies current row to history before writing new state
- active_only query parameter on all list endpoints (default true)
- FastAPI backend with auto-generated OpenAPI 3.1.0 spec at /openapi.json
- Swagger UI at /docs
- SQLite database created automatically at /app/data/zoo.db on first startup
- Single-file Vanilla JS web GUI at / with DE/EN language toggle
- GUI: OrgUnit tree (expandable), Person list, Assignments panel
- GUI: add / edit / end (deactivate) actions for all entities with mutation_reason field
- GUI: show inactive toggle
- GUI: open position displayed with distinct badge
- Podman container support (Containerfile, python:3.13-slim)
- GitHub Actions CI workflow with pip-audit and pytest matrix

### Architecture decisions

- No hard DELETE on any resource; deactivation via PATCH valid_until
- No ORM; raw aiosqlite SQL for full query visibility
- Dependency injection via FastAPI get_db(); in-memory SQLite in tests
- CORS restricted to localhost origins only
