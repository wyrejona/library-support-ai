#!/bin/bash
# Updated watchdog.sh with Heartbeat
API_URL="http://localhost:8000/health"
SERVICE_NAME="library-ai"
LOG_FILE="/home/repository/library-support-ai/watchdog.log"

# Add a heartbeat timestamp
echo "$(date): Heartbeat - Checking service status..." >> $LOG_FILE

STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $STATUS -ne 200 ]; then
    echo "$(date): ALERT - Service is DOWN ($STATUS). Restarting..." >> $LOG_FILE
    sudo systemctl restart $SERVICE_NAME
else
    echo "$(date): OK - Service is healthy." >> $LOG_FILE
fi
