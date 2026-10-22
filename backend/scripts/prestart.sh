#! /usr/bin/env bash

set -e
set -x

# Run migrations
alembic upgrade head

# Create initial data in DB
python app/initial_data.py

python app/seed_demo_users.py
