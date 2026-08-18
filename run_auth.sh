#!/bin/bash

# Check if credentials are provided as arguments or already in environment
if [ -z "$SLACK_CLIENT_ID" ] || [ -z "$SLACK_CLIENT_SECRET" ]; then
    echo "Error: SLACK_CLIENT_ID and SLACK_CLIENT_SECRET must be set."
    echo "Usage: SLACK_CLIENT_ID=xxx SLACK_CLIENT_SECRET=yyy ./run_auth.sh"
    exit 1
fi

# Run the authentication script
python3 auth.py
