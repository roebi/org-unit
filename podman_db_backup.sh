#!/usr/bin/env bash

set -euo pipefail

backup_dir="db_backup"
mkdir -p "$backup_dir"

timestamp=$(date +"%Y%m%d_%H%M")
backup_file="$backup_dir/${timestamp}_org-unit_backup.db"

podman cp org-unit:/app/data/org-unit.db "$backup_file"
echo "Backup written to $backup_file"

