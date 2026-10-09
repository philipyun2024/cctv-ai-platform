#!/usr/bin/env bash
set -e
curl -s http://localhost:8000/health
echo
curl -s http://localhost:8000/api/v1/cameras
echo
curl -s http://localhost:8000/api/v1/alarms
echo
