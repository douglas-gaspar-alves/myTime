#!/bin/bash
# Flatpak entry point for myTime
export PYTHONPATH=/app/share:$PYTHONPATH
exec python3 -m myTime "$@"
