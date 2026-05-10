#!/bin/bash
set -e

echo "🔧 Setting up TaskFlow..."

# Python virtualenv + dependencies
echo "▶ Installing Python dependencies..."
python3 -m venv venv
venv/bin/pip install -r requirements.txt
echo "✅ Python dependencies installed."

# Node.js check
if ! command -v node &>/dev/null; then
  echo "▶ Node.js not found. Installing via nvm..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  nvm install 20
  echo "✅ Node.js installed."
else
  echo "✅ Node.js already installed: $(node --version)"
fi

# Frontend dependencies
echo "▶ Installing frontend dependencies..."
cd frontend && npm install && cd ..
echo "✅ Frontend dependencies installed."

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the app:"
echo "  docker compose up"
