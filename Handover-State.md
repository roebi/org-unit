skill: apply-tdd-loop-en
entry_point: A
language: Python
test_framework: pytest + pytest-asyncio + httpx

requirements:
  - [x] FR-29: DB init creates all 6 tables on startup
  - [x] FR-30: valid_from / valid_until NOT NULL enforced
  - [x] FR-31: valid_until defaults to 9999-12-31
  - [x] FR-32: PATCH copies row to history before update
  - [x] FR-01: POST /org-units creates record -> 201
  - [x] FR-02: POST /org-units without mutation_reason -> 422
  - [x] FR-03: GET /org-units active_only=true (default)
  - [x] FR-04: GET /org-units active_only=false
  - [x] FR-05: GET /org-units/tree returns nested structure
  - [x] FR-06: GET /org-units/{id} -> 200 or 404
  - [x] FR-07: GET /org-units/{id}/history
  - [x] FR-08: PATCH /org-units/{id} updates + copies to history
  - [x] FR-09: PATCH /org-units/{id} without mutation_reason -> 422
  - [x] FR-10: deactivate OrgUnit via PATCH valid_until
  - [x] FR-11: POST /persons creates record -> 201
  - [x] FR-12: POST /persons without mutation_reason -> 422
  - [x] FR-13: GET /persons active_only filter
  - [x] FR-14: GET /persons/{id} -> 200 or 404
  - [x] FR-15: GET /persons/{id}/history
  - [x] FR-16: PATCH /persons/{id} updates + copies to history
  - [x] FR-17: PATCH /persons/{id} without mutation_reason -> 422
  - [x] FR-18: deactivate Person via PATCH valid_until
  - [x] FR-19: POST /assignments creates record -> 201
  - [x] FR-20: POST /assignments without mutation_reason -> 422
  - [x] FR-21: POST /assignments with bad FK -> 422
  - [x] FR-22: GET /assignments active_only filter
  - [x] FR-23: GET /org-units/{id}/assignments
  - [x] FR-24: GET /persons/{id}/assignments
  - [x] FR-25: GET /assignments/{id}/history
  - [x] FR-26: PATCH /assignments/{id} updates + copies to history
  - [x] FR-27: PATCH /assignments/{id} without mutation_reason -> 422
  - [x] FR-28: deactivate Assignment via PATCH valid_until
  - [x] FR-33: GET / serves static HTML
  - [x] FR-34..FR-38: GUI (served as static file, no server-side tests)

current_iteration: complete
current_phase: REFACTOR done
exit_condition_met: true
