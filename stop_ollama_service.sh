#!/bin/bash
echo "=== Stopping Ollama System Service ==="
echo ""

# 1. Stop system service
echo "1. Stopping systemd service..."
sudo systemctl stop ollama.service 2>/dev/null
sudo systemctl disable ollama.service 2>/dev/null

# 2. Stop snap service
echo "2. Stopping snap service..."
sudo snap stop ollama 2>/dev/null
sudo snap disable ollama 2>/dev/null

# 3. Kill any remaining processes
echo "3. Killing remaining processes..."
sudo pkill -9 ollama 2>/dev/null
sudo killall -9 ollama 2>/dev/null

# 4. Free port 11434
echo "4. Freeing port 11434..."
sudo kill -9 $(sudo lsof -t -i:11434 2>/dev/null) 2>/dev/null
sudo fuser -k 11434/tcp 2>/dev/null

# 5. Wait
sleep 3

# 6. Verify
echo "5. Verifying..."
if sudo lsof -i :11434 >/dev/null 2>&1; then
    echo "   ❌ Port 11434 still in use"
    echo "   Running process:"
    sudo lsof -i :11434
else
    echo "   ✅ Port 11434 is free"
fi

if pgrep -x "ollama" >/dev/null; then
    echo "   ❌ Ollama process still running"
    ps aux | grep ollama | grep -v grep
else
    echo "   ✅ No Ollama processes running"
fi

echo ""
echo "=== Done ==="
echo "You can now start Ollama manually with: ollama serve"
