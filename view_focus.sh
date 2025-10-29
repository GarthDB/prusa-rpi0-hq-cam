#!/bin/bash
#
# View Focus Images - Run on your Mac
# Automatically downloads and opens the latest focus test image
#

PI_HOST="${1:-prusa-camera.local}"

echo "=== Camera Focus Viewer ==="
echo "Monitoring: pi@${PI_HOST}"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    # Download latest image
    scp -q "pi@${PI_HOST}:~/focus_test/focus_latest.jpg" /tmp/prusa_focus.jpg 2>/dev/null
    
    if [ $? -eq 0 ]; then
        # Open in Preview (Mac) - will update if already open
        open -a Preview /tmp/prusa_focus.jpg
        echo "$(date +%H:%M:%S) - Updated"
    else
        echo "$(date +%H:%M:%S) - Waiting for images..."
    fi
    
    sleep 3
done

