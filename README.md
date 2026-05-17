# zoo-org

Digitalize the organizational structure (Aufbauorganisation) of a zoo.

Built using the [sw-dev-agent-framework](https://pypi.org/project/sw-dev-agent-framework/)
development process, starting from `concept.md`.

## Development phases

| Phase | Skill | Status | Output |
|-------|-------|--------|--------|
| 1. Requirements | `gather-requirements-en` | in progress | requirements.md |
| 2. Design | `design-architecture-en` | pending | architecture.md |
| 3. Implement | `apply-tdd-loop-en` | pending | src/ + tests/ |
| 4. Review | `code-review-en` | pending | review.md |
| 5. Release | `release-sw-project-en` | pending | tagged release |

## Setup

```bash
uv sync
uv run sw-dev-agent start "Digitalize the organizational structure of a zoo - see concept.md"
```

## Run (Podman)

```bash
podman build -t zoo-org .

podman run -d \
  -p 8000:8000 \
  -v zoo-data:/app/data \
  --name zoo-org \
  zoo-org:latest
```

- OpenAPI spec: http://localhost:8000/openapi.json
- Swagger UI:   http://localhost:8000/docs
- Web GUI:      http://localhost:8000

## Key design decisions

See `concept.md` for the full agreed concept.

Short summary:
- One OrgUnit tree (self-referencing parent_id)
- Flat Person table (no hierarchy)
- Assignment bridge table (N:M, carries role_label)
- No hard delete - deactivate via valid_until
- Bi-temporal: valid_from / valid_until (9999-12-31 = active) / updated_at
- mutation_reason mandatory on every POST and PATCH
- History tables: org_unit_history, person_history, assignment_history
- SQLite in /app/data/zoo.db (Podman volume)
- DE/EN language switch in GUI
