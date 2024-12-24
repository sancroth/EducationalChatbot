#!/bin/bash

ROLE=rasa

# Check the role
if [ "$ROLE" = "action" ]; then
    echo "Starting the Rasa action server..."
    rasa run actions --debug
elif [ "$ROLE" = "rasa" ]; then
    echo "Starting the Rasa server..."
    rasa run --enable-api --cors "*" --port 5005 --debug
else
    echo "Error: ROLE environment variable must be set to 'rasa' or 'action'."
    exit 1
fi
