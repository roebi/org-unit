# Requirements

## Goal Statement

Digitalize the hierarchical organizational structure (Aufbauorganisation) of a zoo
as a FastAPI + SQLite REST service in a Podman container with a single-HTML web GUI.

- Primary user: zoo administrator or HR manager via a web browser
- Core action: manage OrgUnit tree, Person flat list, and Assignment bridge; track full change history
- Target platform: web service (FastAPI + Uvicorn) in a Podman container, port 8000
- Key constraints: Python 3.13, SQLite (aiosqlite), Vanilla JS (no build step), bi-temporal data model, no hard delete, mutation_reason mandatory on all writes, history tables for all 3 entities

---

## Functional Requirements

### OrgUnit

FR-01: Accept POST /api/v1/org-units with fields name, description, parent_id, sort_order, valid_from, valid_until, mutation_reason and persist a new OrgUnit row; return HTTP 201 with the created record.

FR-02: Reject POST /api/v1/org-units that is missing mutation_reason with HTTP 422 before any database write.

FR-03: Return GET /api/v1/org-units as a flat JSON array of OrgUnit records where valid_from <= today AND valid_until >= today when query param active_only=true (default).

FR-04: Return GET /api/v1/org-units?active_only=false as a flat JSON array of all OrgUnit records regardless of date fields.

FR-05: Return GET /api/v1/org-units/tree as a nested JSON tree of active OrgUnits, each node carrying its children array.

FR-06: Return GET /api/v1/org-units/{id} as a single OrgUnit JSON object; return HTTP 404 when id does not exist.

FR-07: Return GET /api/v1/org-units/{id}/history as a JSON array of all rows in org_unit_history for the given id, ordered by replaced_at descending.

FR-08: Accept PATCH /api/v1/org-units/{id} with any subset of updatable fields plus mutation_reason; copy the current org_unit row to org_unit_history with replaced_at = datetime now; write the new state to org_unit with updated_at = datetime now; return HTTP 200 with the updated record.

FR-09: Reject PATCH /api/v1/org-units/{id} that is missing mutation_reason with HTTP 422 before any database write.

FR-10: Deactivate an OrgUnit by sending PATCH /api/v1/org-units/{id} with valid_until set to a date <= today and a mutation_reason; no DELETE endpoint exists on this resource.

### Person

FR-11: Accept POST /api/v1/persons with fields first_name, last_name, email, notes, valid_from, valid_until, mutation_reason and persist a new Person row; return HTTP 201 with the created record.

FR-12: Reject POST /api/v1/persons that is missing mutation_reason with HTTP 422 before any database write.

FR-13: Return GET /api/v1/persons as a flat JSON array; support active_only query param (default true) using the same date range filter as FR-03.

FR-14: Return GET /api/v1/persons/{id} as a single Person JSON object; return HTTP 404 when id does not exist.

FR-15: Return GET /api/v1/persons/{id}/history as a JSON array of all rows in person_history for the given id, ordered by replaced_at descending.

FR-16: Accept PATCH /api/v1/persons/{id} with any subset of updatable fields plus mutation_reason; copy the current person row to person_history with replaced_at = datetime now; write the new state; return HTTP 200.

FR-17: Reject PATCH /api/v1/persons/{id} that is missing mutation_reason with HTTP 422 before any database write.

FR-18: Deactivate a Person by sending PATCH /api/v1/persons/{id} with valid_until set to a date <= today and a mutation_reason; no DELETE endpoint exists on this resource.

### Assignment

FR-19: Accept POST /api/v1/assignments with fields org_unit_id, role_label, valid_from, valid_until, mutation_reason and optional person_id; verify org_unit_id references an existing row; persist the Assignment; return HTTP 201. An assignment without person_id represents an open (unfilled) position.

FR-19b: Accept POST /api/v1/assignments where person_id is omitted or null; the created assignment row stores person_id as NULL and represents a defined but unfilled position in the org structure.

FR-19c: Accept PATCH /api/v1/assignments/{id} where person_id is set to a valid person id to fill an open position, or set to null to vacate a filled position; both operations copy the current row to history first.

FR-20: Reject POST /api/v1/assignments that is missing mutation_reason with HTTP 422 before any database write.

FR-21: Reject POST /api/v1/assignments where org_unit_id does not reference an existing row with HTTP 422. Reject if person_id is provided but does not reference an existing person row with HTTP 422. Do not reject when person_id is omitted or null.

FR-22: Return GET /api/v1/assignments as a flat JSON array; support active_only query param (default true).

FR-23: Return GET /api/v1/org-units/{id}/assignments as a JSON array of all Assignment rows linked to the given org_unit_id; support active_only query param (default true).

FR-24: Return GET /api/v1/persons/{id}/assignments as a JSON array of all Assignment rows linked to the given person_id; support active_only query param (default true).

FR-25: Return GET /api/v1/assignments/{id}/history as a JSON array of all rows in assignment_history for the given id, ordered by replaced_at descending.

FR-26: Accept PATCH /api/v1/assignments/{id} with any subset of updatable fields plus mutation_reason; copy the current assignment row to assignment_history with replaced_at = datetime now; write the new state; return HTTP 200.

FR-27: Reject PATCH /api/v1/assignments/{id} that is missing mutation_reason with HTTP 422 before any database write.

FR-28: Deactivate an Assignment by sending PATCH /api/v1/assignments/{id} with valid_until set to a date <= today and a mutation_reason; no DELETE endpoint exists on this resource.

### Database Initialisation

FR-29: Create the SQLite database file at /app/data/zoo.db and all 6 tables (org_unit, person, assignment, org_unit_history, person_history, assignment_history) on application startup when the file does not yet exist; start without error.

FR-30: Enforce valid_from DATE NOT NULL and valid_until DATE NOT NULL on all 6 tables at the database schema level; never store NULL in either column.

FR-31: Store 9999-12-31 as the sentinel value for valid_until when no end date is planned; the application layer sets this value automatically when valid_until is omitted in a POST request.

FR-32: Before writing any PATCH update to a productive table, copy the complete current row including mutation_reason to the corresponding history table with replaced_at = datetime('now', 'utc').

### Web GUI

FR-33: Serve a single HTML file at GET / that loads the web GUI without a build step; the file must be self-contained (no external CDN dependencies required at runtime).

FR-34: Render an OrgUnit tree panel (left) and a Person list panel (right) side by side; tree nodes are expandable and collapsible.

FR-35: Render an Assignments panel below the tree when an OrgUnit node is selected, listing active assignments with person name and role_label.

FR-36: Provide a DE/EN language toggle button in the GUI header; all UI labels switch language without page reload; user-entered content is not translated.

FR-37: Provide add, edit, and end (deactivate) actions for OrgUnit, Person, and Assignment; every mutation form includes a mandatory mutation_reason input field.

FR-38: Show inactive records (valid_until < today) when the user activates a "show inactive" checkbox; hide them by default (active_only=true).

---

## Non-Functional Requirements

NFR-01: Testability - every API endpoint must have at least one pytest test covering the happy path and at least one test covering the HTTP 422 error path (missing mutation_reason); tests use httpx AsyncClient against an in-memory SQLite test database.

NFR-02: Portability - the application runs on Python 3.13 inside a Podman container built FROM python:3.13-slim; no Docker daemon dependency.

NFR-03: Supply chain - all Python dependencies carry version bounds in pyproject.toml; pip-audit runs in the Containerfile build step and in the GitHub Actions CI workflow.

NFR-04: Data integrity - no DELETE SQL statement is issued against any productive table in any code path; deactivation is the only removal mechanism.

NFR-05: Auditability - every previous state of every entity is preserved in the corresponding history table with replaced_at timestamp and the original mutation_reason; the API exposes /history endpoints for all three entities.

NFR-06: Internationalisation - all field names, API paths, and source code identifiers are English; the GUI supports DE and EN display language at runtime via a toggle.

NFR-07: Reliability - the application starts without error when /app/data/zoo.db does not exist and creates all tables automatically.

NFR-08: CORS - allow_origins is restricted to localhost origins only; wildcard "*" is not used in any deployed configuration.

NFR-09: API contract - FastAPI auto-generates a valid OpenAPI 3.1.0 spec at GET /openapi.json; the Swagger UI is available at GET /docs.

---

## Out of Scope

- Authentication and authorization (no login, no roles, no JWT)
- Org chart PDF or image export
- History viewer in the GUI (history is queryable via API only in v1)
- Person photos or file attachments
- Multi-tenancy
- Audit log beyond history tables
- Email notifications
- Reporting or analytics dashboards

---

## Handover to Design Phase

```yaml
phase: requirements
status: done
output: requirements.md written with 38 functional and 9 non-functional requirements
next: design-architecture-en reads requirements.md and produces architecture.md
```
