#!/usr/bin/env bash
# Generate a self-signed TLS cert for local/dev nginx (certs/server.{crt,key}).
# The private key is gitignored — run this once per machine before
# `docker compose up`. For a real domain on EC2, use Let's Encrypt instead
# (see README).
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)/certs"
mkdir -p "$DIR"

openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout "$DIR/server.key" -out "$DIR/server.crt" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Wrote $DIR/server.crt and $DIR/server.key"
