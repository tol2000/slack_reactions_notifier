#!/bin/bash
docker run -d \
--env-file=.env \
--name=slack-reaction-notifier \
slack-reaction-notifier:v0.0.1
