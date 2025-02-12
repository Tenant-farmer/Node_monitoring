#!/bin/bash

echo "=== Cysic Monitor Bot Installation ==="
echo ""

# Step 1: Check and install system requirements
echo "[1/3] Checking system requirements..."
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    apt update
    apt install -y python3-full python3-pip
fi

if ! command -v screen &> /dev/null; then
    echo "Installing screen..."
    apt install -y screen
fi

# Step 2: Create and activate virtual environment
echo "[2/3] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 3: Install Python packages
echo "Installing required Python packages..."
pip install -r requirements.txt

# Step 4: Create config file
echo "[3/3] Setting up configuration..."
echo ""
echo "Please enter your Telegram bot token (get it from @BotFather):"
read -r token

if [ -f "config.py" ]; then
    echo "Backing up existing config.py to config.py.backup"
    cp config.py config.py.backup
fi

cat > config.py << EOF
TOKEN = "${token}"
ALLOWED_USERS = []  # Add your Telegram user IDs here
EOF

echo ""
echo "Installation completed!"
echo ""
echo "Next steps:"
echo "1. Add your Telegram user ID to ALLOWED_USERS in config.py"
echo "2. Run the bot: python3 monitor.py"
echo ""
echo "To get your Telegram ID, send a message to @userinfobot" 
