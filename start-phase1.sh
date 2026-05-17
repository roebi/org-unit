#!/usr/bin/env bash
# Phase 1 - gather requirements
# Run this from the zoo-org repo root after: uv sync
#
# The sw-dev-agent reads the goal statement and concept.md,
# then produces requirements.md via the gather-requirements-en skill.

set -euo pipefail

echo "=== zoo-org: Phase 1 - Gather Requirements ==="
echo ""
echo "Input:  concept.md (agreed design decisions)"
echo "Output: requirements.md (testable FR / NFR list)"
echo ""

uv run sw-dev-agent start \
  "Digitalize the organizational structure of a zoo using FastAPI + SQLite + Vanilla JS single-HTML frontend in a Podman container. See concept.md for all agreed design decisions including the bi-temporal data model, soft-delete pattern, mutation_reason, history tables, and API design."

echo ""
echo "Phase 1 done. Check requirements.md, then run design phase."
