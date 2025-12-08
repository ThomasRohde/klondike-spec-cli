#!/bin/bash
# Long-Running Agent Environment Initialization Script
# This script sets up the development environment for agent sessions

set -e  # Exit on any error

# Configuration - adjust these for your project
DEV_PORT=3000  # Change to match your dev server port

echo "🚀 Starting development environment..."
echo "================================================"

# 1. Check prerequisites
echo ""
echo "📋 Checking prerequisites..."

# Node.js project:
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi
echo "   ✅ Node.js $(node -v)"

# Python project:
# if ! command -v python3 &> /dev/null; then
#     echo "❌ Python 3 is required but not installed"
#     exit 1
# fi
# echo "   ✅ Python $(python3 --version)"

# 2. Kill any stale dev servers on target port
echo ""
echo "🔍 Checking for stale processes on port $DEV_PORT..."
if command -v lsof &> /dev/null; then
    STALE_PID=$(lsof -ti:$DEV_PORT 2>/dev/null || true)
    if [ -n "$STALE_PID" ]; then
        echo "  Killing stale process PID: $STALE_PID"
        kill -9 $STALE_PID 2>/dev/null || true
        sleep 1
        echo "   ✅ Stale processes cleaned up"
    else
        echo "   ✅ No stale processes found"
    fi
else
    echo "⚠ lsof not available, skipping stale process check"
fi

# 3. Install dependencies
echo ""
echo "📦 Installing dependencies..."

# Node.js project:
if [ ! -d "node_modules" ]; then
    if ! npm install; then
        echo "❌ Dependency installation failed!"
        exit 1
    fi
else
    echo "   ✅ Dependencies already installed"
fi

# Python project:
# pip install -r requirements.txt

# 4. Start development server in BACKGROUND
echo ""
echo "🖥️  Starting development server in background..."

# Node.js project:
npm run dev > .dev-server.log 2>&1 &
DEV_PID=$!
echo $DEV_PID > .dev-server.pid
echo "   Started dev server in background (PID: $DEV_PID)"

# 5. Wait for server to be ready (with timeout)
echo ""
echo "⏳ Waiting for server to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
SERVER_READY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ] && [ "$SERVER_READY" = false ]; do
    sleep 1
    ATTEMPT=$((ATTEMPT + 1))
    if command -v curl &> /dev/null; then
        if curl -s -o /dev/null -w '' "http://localhost:$DEV_PORT" 2>/dev/null; then
            SERVER_READY=true
        fi
    elif command -v nc &> /dev/null; then
        if nc -z localhost $DEV_PORT 2>/dev/null; then
            SERVER_READY=true
        fi
    fi
done

if [ "$SERVER_READY" = false ]; then
    echo "❌ Server failed to start within 30 seconds!"
    echo "   Check .dev-server.log for details"
    exit 1
fi

echo "   ✅ Dev server ready on port $DEV_PORT"

# 6. Health check
echo ""
echo "🏥 Running health check..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$DEV_PORT" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ Health check passed (HTTP 200)"
    else
        echo "❌ Health check failed (HTTP $HTTP_CODE)"
        exit 1
    fi
else
    echo "⚠ curl not available, skipping health check"
fi

# 7. Success message
echo ""
echo "================================================"
echo "✅ Environment ready!"
echo ""
echo "📍 Server running at: http://localhost:$DEV_PORT"
echo "📖 To view output: tail -f .dev-server.log"
echo "📖 To stop: kill \$(cat .dev-server.pid)"
echo ""
echo "🎯 Ready for coding session."
echo "================================================"
