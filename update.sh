#!/bin/bash
set -e
cd "$(dirname "$0")"

git fetch origin main
git pull origin main
docker compose up -d --build