#!/bin/bash
# IMS PRO One-Click Deployment Script for VPS (e.g. 94.23.120.156)
# Binds IMS PRO to port 80 so accessing http://94.23.120.156 opens IMS PRO directly.

set -e
echo "=========================================================="
echo "   🚀 IMS PRO - Automatic VPS Installation & Deployment"
echo "=========================================================="

# 1. Update system & install Node.js if missing
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs git
fi

# 2. Install dependencies & PM2 process manager
echo "📦 Installing application dependencies..."
npm install --production=false
if ! command -v pm2 &> /dev/null; then
    npm install -g pm2
fi

# 3. Build production bundle
echo "🔨 Building production server..."
npm run build

# 4. Stop old process if running
pm2 delete imspro 2>/dev/null || true

# 5. Start IMS PRO on Port 80
echo "🚀 Starting IMS PRO on Port 80..."
PORT=80 HOST=0.0.0.0 pm2 start server.js --name "imspro"
pm2 save

echo "=========================================================="
echo "✅ IMS PRO is now LIVE on your VPS!"
echo "🌐 URL: http://94.23.120.156"
echo "🔑 Login: http://94.23.120.156/ints/login"
echo "=========================================================="
