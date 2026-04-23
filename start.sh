#!/bin/bash
# start.sh — Run the Jobandu backend with the OpenSSL compatibility fix
# Usage: ./start.sh
#
# Why this is needed:
#   OpenSSL 3.5+ (installed via system update) raised its default security
#   level to 2, which causes "TLSV1_ALERT_INTERNAL_ERROR" when connecting
#   to MongoDB Atlas. Our local openssl.cnf sets SECLEVEL=1 to fix this.

# cd "$(dirname "$0")"   # make sure we're always in the project directory

# source venv/bin/activate

# export OPENSSL_CONF="$(pwd)/openssl.cnf"

# echo "Using OpenSSL config: $OPENSSL_CONF"
# uvicorn main:app --reload
