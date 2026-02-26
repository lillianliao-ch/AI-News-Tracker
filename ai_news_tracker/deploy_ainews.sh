#!/bin/bash
set -e

# Configuration
SERVER_IP="43.132.170.185"
SERVER_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/ai_news_tracker"
LOCAL_DIR="$(pwd)"
SSH_PASS="TRuproyaya@123"

echo "🚀 Deploying AI News Tracer to Tencent Cloud ($SERVER_IP)..."

# Check for sshpass
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass is not installed. Please install it:"
    echo "   brew install sshpass"
    exit 1
fi

# 1. Sync files to server
echo "📂 Syncing files..."
sshpass -p "$SSH_PASS" rsync -avz \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='data/*.db' \
    --exclude='.git' \
    --exclude='.DS_Store' \
    --exclude='__pycache__' \
    -e "ssh -o StrictHostKeyChecking=no" \
    $LOCAL_DIR/ $SERVER_USER@$SERVER_IP:$REMOTE_DIR/

# 2. Deploy on server
echo "🐳 Deploying on host..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
    cd $REMOTE_DIR
    
    # Create data directory if not exists
    mkdir -p data
    mkdir -p logs

    # Check if .env exists, if not create from example
    if [ ! -f .env ]; then
        cp backend/.env.example .env
        echo "⚠️  Created .env from example. Please configure API keys on server!"
    fi

    # --- Python Backend ---
    echo "🐍 Setting up Backend..."
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    cd backend
    pip install -r requirements.txt
    cd ..

    # --- Node Frontend ---
    echo "📦 Setting up Frontend..."
    # Ensure Node 20 is there (from previous deploy)
    if ! command -v node &> /dev/null; then
         echo "❌ Node.js not found! Please install Node 20."
         exit 1
    fi
    
    cd frontend
    # Clean potential rogue files that break build
    rm -f src/components/tsconfig.json
    rm -rf dist

    npm install
    # Set public env var for build time (Astro inlines it)
    export PUBLIC_API_URL="http://$SERVER_IP:8002"
    npm run build
    cd ..

    # --- Restart Services ---
    echo "🔄 Restarting Services..."
    
    # Kill existing processes
    pkill -f "uvicorn main:app" || true
    pkill -f "python backend/main.py" || true
    pkill -f "node dist/server/entry.mjs" || true

    # Start Backend
    # Load env vars
    export \$(grep -v '^#' .env | xargs)
    export PORT=8002
    export DATABASE_URL="sqlite:////home/ubuntu/ai_news_tracker/data/ai_news.db"
    
    cd backend
    nohup ../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8002 > ../logs/backend.log 2>&1 &
    cd ..

    # Start Frontend
    export PORT=4321
    export HOST=0.0.0.0
    export VITE_API_BASE_URL="http://localhost:8002/api" # SSR specific
    
    cd frontend
    nohup node dist/server/entry.mjs > ../logs/frontend.log 2>&1 &
    cd ..

    echo "✅ Deployment script finished. Verifying..."
    sleep 5
    if pgrep -f "node dist/server/entry.mjs" > /dev/null; then
        echo "✅ Frontend is running!"
    else
        echo "❌ Frontend failed to start. Check logs/frontend.log"
    fi
EOF

echo "✨ Deployment complete! Access at http://$SERVER_IP:4321"
