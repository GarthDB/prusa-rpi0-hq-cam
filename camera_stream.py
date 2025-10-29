#!/usr/bin/env python3
"""
Camera MJPEG Livestream Server
Streams camera feed over HTTP for viewing in Home Assistant or web browser
"""
import io
import time
import subprocess
import logging
from threading import Thread, Event
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import os

# Load environment variables
def load_env():
    """Load .env file if it exists"""
    env_file = Path(__file__).parent / '.env'
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    env_vars[key.strip()] = value
    
    return env_vars

env_vars = load_env()

# Configuration
STREAM_WIDTH = int(env_vars.get('STREAM_WIDTH', '1280'))
STREAM_HEIGHT = int(env_vars.get('STREAM_HEIGHT', '720'))
STREAM_FPS = int(env_vars.get('STREAM_FPS', '15'))
STREAM_PORT = int(env_vars.get('STREAM_PORT', '8080'))
STREAM_QUALITY = int(env_vars.get('STREAM_QUALITY', '80'))

# Detect camera command
CAMERA_CMD = 'rpicam-vid' if os.system('which rpicam-vid > /dev/null 2>&1') == 0 else 'libcamera-vid'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CameraStream')

class StreamingHandler(BaseHTTPRequestHandler):
    """HTTP handler for MJPEG stream"""
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            # Serve simple viewer page
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_viewer_page().encode('utf-8'))
        
        elif self.path == '/stream':
            # Serve MJPEG stream
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            
            try:
                self.stream_video()
            except Exception as e:
                logger.error(f"Stream error: {e}")
        
        else:
            self.send_error(404)
    
    def stream_video(self):
        """Stream video using rpicam-vid"""
        logger.info("Starting video stream")
        
        cmd = [
            CAMERA_CMD,
            '--width', str(STREAM_WIDTH),
            '--height', str(STREAM_HEIGHT),
            '--framerate', str(STREAM_FPS),
            '--codec', 'mjpeg',
            '--quality', str(STREAM_QUALITY),
            '-t', '0',  # Run indefinitely
            '-n',  # No preview
            '-o', '-'  # Output to stdout
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=10**8
            )
            
            # Read and send frames
            while True:
                # Read until we find a JPEG start marker
                data = process.stdout.read(2)
                if not data or data != b'\xff\xd8':
                    if not data:
                        break
                    continue
                
                # Read until we find JPEG end marker
                frame = b'\xff\xd8'
                while True:
                    byte = process.stdout.read(1)
                    if not byte:
                        break
                    frame += byte
                    if len(frame) >= 2 and frame[-2:] == b'\xff\xd9':
                        break
                
                if not frame or len(frame) < 100:
                    continue
                
                # Send frame
                try:
                    self.wfile.write(b'--FRAME\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n')
                    self.wfile.write(f'Content-Length: {len(frame)}\r\n\r\n'.encode())
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    break
            
            process.terminate()
            process.wait()
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        
        logger.info("Stream ended")
    
    def get_viewer_page(self):
        """Return HTML viewer page"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Prusa Camera Stream</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #fff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        h1 {{
            margin: 0 0 20px 0;
            font-size: 24px;
            font-weight: 500;
        }}
        .stream-container {{
            max-width: 100%;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        img {{
            display: block;
            max-width: 100%;
            height: auto;
        }}
        .info {{
            margin-top: 20px;
            padding: 15px;
            background: #2a2a2a;
            border-radius: 8px;
            font-size: 14px;
            max-width: 600px;
        }}
        .info div {{
            margin: 5px 0;
        }}
        .label {{
            color: #888;
            display: inline-block;
            width: 120px;
        }}
    </style>
</head>
<body>
    <h1>🎥 Prusa Camera Stream</h1>
    <div class="stream-container">
        <img src="/stream" alt="Camera Stream">
    </div>
    <div class="info">
        <div><span class="label">Resolution:</span>{STREAM_WIDTH}x{STREAM_HEIGHT}</div>
        <div><span class="label">Frame Rate:</span>{STREAM_FPS} FPS</div>
        <div><span class="label">Stream URL:</span>http://prusa-camera.local:{STREAM_PORT}/stream</div>
        <div><span class="label">For Home Assistant:</span>Add as Generic Camera with stream URL above</div>
    </div>
</body>
</html>
        """

class StreamingServer:
    """MJPEG streaming server"""
    
    def __init__(self):
        self.server = None
    
    def start(self):
        """Start the streaming server"""
        logger.info(f"Starting camera stream server on port {STREAM_PORT}")
        logger.info(f"Resolution: {STREAM_WIDTH}x{STREAM_HEIGHT} @ {STREAM_FPS}fps")
        logger.info(f"View at: http://prusa-camera.local:{STREAM_PORT}/")
        logger.info(f"Stream URL: http://prusa-camera.local:{STREAM_PORT}/stream")
        
        try:
            self.server = HTTPServer(('0.0.0.0', STREAM_PORT), StreamingHandler)
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            if self.server:
                self.server.shutdown()
        except Exception as e:
            logger.error(f"Server error: {e}")

def main():
    """Main entry point"""
    print("=" * 60)
    print("Prusa Camera MJPEG Livestream Server")
    print("=" * 60)
    print()
    print(f"Stream will be available at:")
    print(f"  View in browser: http://prusa-camera.local:{STREAM_PORT}/")
    print(f"  Direct stream:   http://prusa-camera.local:{STREAM_PORT}/stream")
    print()
    print(f"Configuration:")
    print(f"  Resolution: {STREAM_WIDTH}x{STREAM_HEIGHT}")
    print(f"  Frame Rate: {STREAM_FPS} FPS")
    print(f"  Quality:    {STREAM_QUALITY}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    server = StreamingServer()
    server.start()

if __name__ == '__main__':
    main()

