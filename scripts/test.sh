#! /usr/bin/env sh

# Exit in case of error
set -e
set -x

if docker compose version > /dev/null 2>&1; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi

$COMPOSE build backend
$COMPOSE down -v --remove-orphans # Remove possibly previous broken stacks left hanging after an error
$COMPOSE up -d --wait db mailpit
$COMPOSE run --rm backend bash scripts/prestart.sh
$COMPOSE run --rm -v "$(pwd)/backend/tests:/app/backend/tests" backend bash scripts/tests-start.sh "$@"
$COMPOSE down -v --remove-orphans
