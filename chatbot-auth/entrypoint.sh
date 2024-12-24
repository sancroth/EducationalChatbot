#!/bin/bash

export $(cat .env | xargs)

echo "Starting the Auth server with the following configuration:"
echo "DB_HOST: ${DB_HOST}"
echo "DB_USER: ${DB_USER}"
echo "DB_PASSWORD: <<REDACTED>>"
echo "DB_PORT: ${DB_PORT}"
echo "DB_NAME: ${DB_NAME}"

if [[ -z "${DB_HOST}" || -z "${DB_USER}" || -z "${DB_PASSWORD}" || -z "${DB_PORT}" || -z "${DB_NAME}" ]]; then
    echo "Error: One or more required environment variables are missing."
    exit 1
fi

# Start the Flask application
echo "Starting the Flask application..."
python main.py