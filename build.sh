#!/usr/bin/env bash

docker build -f ./backend/Demo_Dockerfile -t spex.backend:latest .
docker tag spex.backend:latest ghcr.io/genentech/spex.backend:latest
docker push ghcr.io/genentech/spex.backend:latest