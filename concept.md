# Zoo Org Structure - Concept

## Goal

Digitalize the hierarchical organizational structure (Aufbauorganisation) of a zoo.
Reference: https://de.wikipedia.org/wiki/Aufbauorganisation#Stellengestaltung

All code, field names, and API paths are **English**.
The GUI supports a DE/EN language switch. Content (names, descriptions) is user-defined.

---

## Core Rules

- **No hard delete** - ever. Records are deactivated via `valid_until`.
- **No NULL in date fields** - sentinel `9999-12-31` means "still active".
- **No shortcut relations** - a Person has no `org_unit_id`. Always go through Assignment.
- **Productive tables hold current records only** - replaced records move to history tables.

---

## Data Model

### Productive Tables

**OrgUnit** - one self-referencing tree

| Field        | Type              | Notes                                   |
|--------------|-------------------|-----------------------------------------|
| id           | INTEGER PK        | Auto-increment                          |
| name         | TEXT NOT NULL     | Display name                            |
| description  | TEXT              | Optional free text                      |
| parent_id    | INTEGER           | FK -> OrgUnit.id; NULL = root node      |
| sort_order   | INTEGER NOT NULL  | Sibling order within same parent        |
| valid_from      | DATE NOT NULL     | Business start date                     |
| valid_until     | DATE NOT NULL     | Business end date; 9999-12-31 = active  |
| updated_at      | DATETIME NOT NULL | Last write to DB                        |
| mutation_reason | TEXT NOT NULL     | Why this record was created or changed  |

**Person** - flat table, no hierarchy

| Field        | Type              | Notes                                              |
|--------------|-------------------|----------------------------------------------------|
| id           | INTEGER PK        | Auto-increment                                     |
| first_name   | TEXT NOT NULL     |                                                    |
| last_name    | TEXT NOT NULL     |                                                    |
| email        | TEXT              | Optional                                           |
| notes        | TEXT              | Optional free text                                 |
| valid_from      | DATE NOT NULL     | Entry date (Eintrittsdatum)                        |
| valid_until     | DATE NOT NULL     | Exit date (Austrittsdatum); 9999-12-31 = active    |
| updated_at      | DATETIME NOT NULL | Last write to DB                                   |
| mutation_reason | TEXT NOT NULL     | Why this record was created or changed             |

**Assignment** - bridge between OrgUnit and Person

| Field        | Type              | Notes                                   |
|--------------|-------------------|-----------------------------------------|
| id           | INTEGER PK        | Auto-increment                          |
| org_unit_id  | INTEGER NOT NULL  | FK -> OrgUnit.id                        |
| person_id    | INTEGER NOT NULL  | FK -> Person.id                         |
| role_label   | TEXT              | e.g. "Head", "Deputy", "Intern"         |
| valid_from      | DATE NOT NULL     | Assignment start date                   |
| valid_until     | DATE NOT NULL     | Assignment end date; 9999-12-31 = active|
| updated_at      | DATETIME NOT NULL | Last write to DB                        |
| mutation_reason | TEXT NOT NULL     | Why this record was created or changed  |

---

### History Tables

Every UPDATE on a productive table first copies the current row to the corresponding
history table with `replaced_at = now()`, then writes the new state to the productive table.

History tables are exact mirrors of the productive tables plus one field:

- **org_unit_history**    = OrgUnit    + `replaced_at DATETIME NOT NULL`
- **person_history**      = Person     + `replaced_at DATETIME NOT NULL`
- **assignment_history**  = Assignment + `replaced_at DATETIME NOT NULL`

The `mutation_reason` travels with every row into history, so each version
explains why it existed. The `replaced_at` explains when it was superseded.

**Update flow:**
```
PATCH /org-units/5  { name: "Big Cats", mutation_reason: "Corrected category" }
  1. copy current OrgUnit(id=5) -> org_unit_history (replaced_at = now())
  2. write new state -> org_unit (updated_at = now())
```

History then reads as a clear story:
```
org_unit_history id=5:
  name="Big Cats Dept"  mutation_reason="Initial setup"      replaced_at=2026-01-01
  name="Big Cats"       mutation_reason="Shortened name"     replaced_at=2026-03-15

org_unit id=5 (current):
  name="Big Cats Unit"  mutation_reason="Corrected category" updated_at=2026-05-15
```

**Future cleanup:**
```sql
DELETE FROM org_unit_history   WHERE replaced_at < :cutoff_date;
DELETE FROM person_history     WHERE replaced_at < :cutoff_date;
DELETE FROM assignment_history WHERE replaced_at < :cutoff_date;
```

---

## Bi-Temporal Pattern

Every entity carries two independent time axes:

| Axis          | Fields                   | Meaning                               |
|---------------|--------------------------|---------------------------------------|
| Business time | valid_from / valid_until | When is it true in the organization   |
| Technical time| updated_at / replaced_at | When was it written to the DB         |

Example: enter today (2026-05-15) a new OrgUnit that starts 2027-01-01:
```
valid_from       = 2027-01-01               <- business reality
valid_until      = 9999-12-31               <- no end planned
updated_at       = 2026-05-15               <- technical: when you typed it
mutation_reason  = "Planned restructuring"  <- why it was created
```

Active record query (same pattern for all entities):
```sql
WHERE valid_from <= :today AND valid_until >= :today
```

---

## API Design (OpenAPI 3.1.0)

Base path: `/api/v1`

**No DELETE endpoint on any resource.**
To deactivate: PATCH with `valid_until = today` (or the actual business end date).

**`mutation_reason` is mandatory in every POST and PATCH request body.**
Requests without it are rejected (HTTP 422). No defaults, no fallbacks.

### OrgUnit

| Method | Path                     | Description                               |
|--------|--------------------------|-------------------------------------------|
| GET    | /org-units               | List flat; query: active_only=true        |
| GET    | /org-units/tree          | Nested tree                               |
| GET    | /org-units/{id}          | Single record                             |
| GET    | /org-units/{id}/history  | All replaced versions                     |
| POST   | /org-units               | Create                                    |
| PATCH  | /org-units/{id}          | Update (copies to history first)          |

### Person

| Method | Path                   | Description                               |
|--------|------------------------|-------------------------------------------|
| GET    | /persons               | List; query: active_only=true             |
| GET    | /persons/{id}          | Single record                             |
| GET    | /persons/{id}/history  | All replaced versions                     |
| POST   | /persons               | Create                                    |
| PATCH  | /persons/{id}          | Update (copies to history first)          |

### Assignment

| Method | Path                           | Description                         |
|--------|--------------------------------|-------------------------------------|
| GET    | /assignments                   | List; query: active_only=true       |
| GET    | /org-units/{id}/assignments    | All assignments for one OrgUnit     |
| GET    | /persons/{id}/assignments      | All assignments for one Person      |
| GET    | /assignments/{id}/history      | All replaced versions               |
| POST   | /assignments                   | Create                              |
| PATCH  | /assignments/{id}              | Update (copies to history first)    |

---

## Tech Stack

| Layer      | Choice                         | Rationale                              |
|------------|--------------------------------|----------------------------------------|
| Runtime    | Podman container               | Required constraint                    |
| Backend    | FastAPI + Uvicorn              | Auto-generates OpenAPI 3.1.0 spec      |
| Database   | SQLite via aiosqlite           | Zero extra containers; single file     |
| Frontend   | Single HTML file, Vanilla JS   | KISS; no build step                    |
| Dep mgmt   | uv + pyproject.toml            | Supply chain rules                     |
| Python     | 3.13                           | CI matrix standard                     |

---

## Project Layout

```
zoo-org/
  Containerfile
  pyproject.toml
  src/
    main.py
    database.py
    routers/
      org_units.py
      persons.py
      assignments.py
    models/
      org_unit.py
      person.py
      assignment.py
  static/
    index.html            <- Web GUI (single file, DE/EN switch)
  data/
    .gitkeep              <- zoo.db created here on first startup
```

---

## Container Run

```bash
podman build -t zoo-org .

podman run -d \
  -p 8000:8000 \
  -v zoo-data:/app/data \
  --name zoo-org \
  zoo-org:latest
```

- OpenAPI spec: `http://localhost:8000/openapi.json`
- Swagger UI:   `http://localhost:8000/docs`
- Web GUI:      `http://localhost:8000`

---

## Web GUI (v1 scope)

```
+----------------------+----------------------+
|  Org Tree    [DE|EN] |  Persons             |
|  [+ Add unit]        |  [+ Add person]      |
|                      |                      |
|  > Zoo Direction     |  Smith, John  [edit] |
|    > Animal Care     |  Muster, Hans [edit] |
|      Big Cats [edit] |  ...                 |
|      Primates [edit] |                      |
+----------------------+                      |
|  Assignments: Big Cats                      |
|  [+ Assign person]                          |
|  - Muster, Hans  (Head)    [end]            |
|  - Smith, John   (Deputy)  [end]            |
|  [ ] show inactive                          |
+---------------------------------------------+
```

"end" = PATCH `valid_until = today` on the assignment. No delete.

---

## Not in Scope (v1)

- Authentication / authorization
- Org chart PDF / image export
- History viewer in GUI (history tables queryable via API only)
- Person photos / file uploads
- Multi-tenancy
