#!/bin/bash
# =========================================================================
# MediOps AWS EC2 Deployment Script
# Run this script on a fresh Ubuntu 22.04 LTS instance
# =========================================================================

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting MediOps AWS Deployment Setup..."

# 1. Update system and install dependencies
echo "📦 Updating system and installing dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git curl

# 2. Set up application directory
APP_DIR="/var/www/mediops"
echo "📁 Setting up application directory at $APP_DIR..."
sudo mkdir -p $APP_DIR
sudo chown -R ubuntu:ubuntu $APP_DIR

# 3. Clone the repository (you should run this manually if it's a private repo, 
# or clone it first and just run this script from inside the repo)
# If running this from inside an already cloned repo:
cp -r ./* $APP_DIR/ || echo "Assuming code is already in $APP_DIR"
cd $APP_DIR

# 4. Set up Python Virtual Environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating default .env file..."
    cp .env.example .env
    echo "⚠️ Make sure to edit $APP_DIR/.env with your API keys later!"
fi

# 6. Configure Systemd Service (keeps FastAPI running 24/7)
echo "⚙️ Configuring Systemd service..."
sudo cp scripts/mediops.service /etc/systemd/system/mediops.service
sudo systemctl daemon-reload
sudo systemctl enable mediops
sudo systemctl start mediops

# 7. Configure Nginx (Reverse Proxy)
echo "🌐 Configuring Nginx..."
sudo cp scripts/nginx.conf /etc/nginx/sites-available/mediops
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/mediops /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 8. Set correct permissions for SQLite database and logs
echo "🔒 Setting permissions for SQLite..."
sudo chown -R ubuntu:www-data $APP_DIR
sudo chmod -R 775 $APP_DIR
if [ -f health_app.db ]; then
    sudo chmod 664 health_app.db
fi

echo "✅ Deployment setup complete!"
echo "🌐 Your app should now be live at http://YOUR_EC2_PUBLIC_IP"
