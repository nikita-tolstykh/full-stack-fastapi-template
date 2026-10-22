#! /usr/bin/env bash

# Exit in case of error
set -e

docker-compose down -v --remove-orphans # Remove possibly previous broken stacks left hanging after an error

if [ $(uname -s) = "Linux" ]; then
    echo "Remove __pycache__ files"
    sudo find . -type d -name __pycache__ -exec rm -r {} \+
fi

docker-compose build backend
docker-compose up -d --wait db mailpit
docker-compose run --rm backend bash scripts/prestart.sh
docker-compose run --rm -v "$(pwd)/backend/tests:/app/backend/tests" backend bash scripts/tests-start.sh "$@"
