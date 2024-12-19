#!/bin/sh
cd "$(dirname "$0")"

docker-compose build --no-cache
