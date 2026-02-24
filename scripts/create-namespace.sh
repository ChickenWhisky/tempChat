#!/bin/bash
set -ex

# Wait for Temporal server to be reachable
echo "Waiting for temporal to start..."
until nc -z temporal 7233; do
  sleep 1
done

temporal operator namespace create ${DEFAULT_NAMESPACE} || true
