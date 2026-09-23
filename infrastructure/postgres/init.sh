#!/bin/sh
set -eu
for service in catalog inventory rental customers billing maintenance auth; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres --set=password="$POSTGRES_PASSWORD" --set=service="$service" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'service', :'password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'service')\gexec
SELECT format('CREATE DATABASE %I OWNER %I', :'service', :'service')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'service')\gexec
REVOKE CONNECT ON DATABASE :"service" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"service" TO :"service";
SQL
done
