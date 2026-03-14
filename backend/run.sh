#!/bin/bash
cd "$(dirname "$0")"
exec ./venv/bin/uvicorn main:app --reload
