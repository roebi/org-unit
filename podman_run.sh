#!/usr/bin/env bash

podman run -d -p 8000:8000 -v org-unit-data:/app/data --name org-unit org-unit:latest

