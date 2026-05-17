#!/usr/bin/env bash

podman run -d -p 8000:8000 -v zoo-data:/app/data --name zoo-org zoo-org:latest

