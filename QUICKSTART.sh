#!/bin/bash

# Jarvis Quick Start Script

echo "🤖 Jarvis - Getting Started"
echo "============================"
echo ""

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please fill in your API keys in .env"
fi

echo ""
echo "📦 Installing dependencies..."
echo ""

# Backend
echo "Backend setup..."
cd backend 2>/dev/null || mkdir -p backend
cd ..

python -m venv venv
source venv/bin/activate

pip install -r requirements_backend.txt

# Frontend
echo ""
echo "Frontend setup..."
cd frontend 2>/dev/null || mkdir -p frontend
cd ..

# Docker approach (optional)
echo ""
echo "🐳 Starting with Docker Compose..."
echo "docker-compose up"
echo ""
echo "Or manually:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend"
echo "  python -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r ../requirements_backend.txt"
echo "  uvicorn backend_main:app --reload --port 8000"
echo ""
echo "Terminal 2 - Frontend:"
echo "  npm install"
echo "  npm run dev"
echo ""
echo "✓ Ready! Open http://localhost:5173"
