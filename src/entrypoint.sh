#!/usr/bin/env bash
echo "Starting uvicorn..."
exec uvicorn main:app --host "" --port 9020
