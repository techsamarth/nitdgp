#!/bin/bash
set -e

APP_DIR="/home/samarthseh/nitdgp"
VENV_DIR="$APP_DIR/venv"
APP_FILE="app:app"

echo "🔴 Stopping any running waitress processes..."
pkill -f waitress-serve || true

echo "🧹 Removing old waitress installation..."
$VENV_DIR/bin/pip uninstall -y waitress || true

echo "📦 Reinstalling waitress..."
$VENV_DIR/bin/pip install waitress

echo "🚀 Starting waitress server..."
cd $APP_DIR
nohup $VENV_DIR/bin/waitress-serve --host=127.0.0.1 --port=5000 $APP_FILE > waitress.log 2>&1 &

echo "✅ Waitress restarted. Logs available at $APP_DIR/waitress.log"
