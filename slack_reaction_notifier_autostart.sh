#!/bin/bash

# Check if container can be started, run new one if it does not exist
if ! docker start slack-reaction-notifier > /dev/null 2>&1; then
    docker run --name=slack-reaction-notifier slack-reaction-notifier:v0.0.1 > /dev/null 2>&1 &
fi
