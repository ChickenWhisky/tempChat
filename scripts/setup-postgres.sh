#!/bin/bash
set -ex

# Wait for DB to be reachable
echo "Waiting for postgresql to start..."
until nc -z ${POSTGRES_SEEDS} ${DB_PORT}; do
  sleep 1
done

# Setup Temporal DB
temporal-sql-tool --plugin postgres12 --ep ${POSTGRES_SEEDS} -p ${DB_PORT} -u ${POSTGRES_USER} --pw ${POSTGRES_PWD} --db temporal create
temporal-sql-tool --plugin postgres12 --ep ${POSTGRES_SEEDS} -p ${DB_PORT} -u ${POSTGRES_USER} --pw ${POSTGRES_PWD} --db temporal setup-schema -v 0.0
temporal-sql-tool --plugin postgres12 --ep ${POSTGRES_SEEDS} -p ${DB_PORT} -u ${POSTGRES_USER} --pw ${POSTGRES_PWD} --db temporal update -schema-dir /etc/temporal/schema/postgresql/v12/temporal/versioned

# Setup Temporal Visibility DB
temporal-sql-tool --plugin postgres12 --ep ${POSTGRES_SEEDS} -p ${DB_PORT} -u ${POSTGRES_USER} --pw ${POSTGRES_PWD} --db temporal_visibility create
temporal-sql-tool --plugin postgres12 --ep ${POSTGRES_SEEDS} -p ${DB_PORT} -u ${POSTGRES_USER} --pw ${POSTGRES_PWD} --db temporal_visibility setup-schema -v 0.0
temporal-sql-tool --plugin postgres12 --ep ${POSTGRES_SEEDS} -p ${DB_PORT} -u ${POSTGRES_USER} --pw ${POSTGRES_PWD} --db temporal_visibility update -schema-dir /etc/temporal/schema/postgresql/v12/visibility/versioned
