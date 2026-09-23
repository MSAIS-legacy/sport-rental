#!/bin/sh
# Доставка ephemeral JWT-ключей в удалённый Docker daemon (GitLab dind).
set -eu
project="${COMPOSE_PROJECT_NAME:-sport-rental}"
docker create --name rental-ci-keys \
  -v "${project}_ci-public:/public" -v "${project}_ci-private:/private" \
  python:3.13-slim >/dev/null
trap 'docker rm -f rental-ci-keys >/dev/null 2>&1 || true' EXIT
docker cp .secrets/public.pem rental-ci-keys:/public/public.pem
docker cp .secrets/private.pem rental-ci-keys:/private/private.pem
