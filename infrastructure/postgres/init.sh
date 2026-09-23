#!/bin/sh
set -eu
for service in catalog inventory rental customers billing maintenance auth; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres --set=password="$POSTGRES_PASSWORD" --set=service="$service" <<'SQL'
CREATE USER :"service" WITH PASSWORD :'password';
CREATE DATABASE :"service" OWNER :"service";
REVOKE CONNECT ON DATABASE :"service" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"service" TO :"service";
SQL
done
