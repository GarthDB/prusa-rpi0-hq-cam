#!/bin/bash
#
# Focus Test Script
# Rapidly captures test images for focusing the camera
#

echo "=== Camera Focus Test Tool ==="
echo ""
echo "This will capture test images every 2 seconds."
echo "Images saved to: ~/focus_test/"
echo ""
echo "Instructions:"
echo "  1. Position camera pointing at printer bed"
echo "  2. Run this script"
echo "  3. In another terminal, watch images with: watch -n 1 'ls -lth ~/focus_test/ | head'"
echo "  4. Copy latest image to view: scp pi@prusa-camera.local:~/focus_test/focus_latest.jpg ."
echo "  5. Adjust focus dial until sharp"
echo "  6. Press Ctrl+C when done"
echo ""
read -p "Press Enter to start..."

# Create directory
mkdir -p ~/focus_test
cd ~/focus_test

# Detect camera command
if command -v rpicam-still &> /dev/null; then
    CAM_CMD="rpicam-still"
else
    CAM_CMD="libcamera-still"
fi

echo ""
echo "Starting focus test (Ctrl+C to stop)..."
echo ""

# Counter
COUNT=0

while true; do
    COUNT=$((COUNT + 1))
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    FILENAME="focus_${TIMESTAMP}.jpg"
    
    echo -n "[$COUNT] Capturing ${FILENAME}... "
    
    # Capture with fast settings
    $CAM_CMD \
        -o "$FILENAME" \
        --width 1920 \
        --height 1080 \
        -t 500 \
        -n \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        # Also save as "latest" for easy access
        cp "$FILENAME" "focus_latest.jpg"
        SIZE=$(du -h "$FILENAME" | cut -f1)
        echo "✓ ($SIZE)"
    else
        echo "✗ Failed"
    fi
    
    # Wait 2 seconds
    sleep 2
done

