#!/usr/bin/env python3
"""
Simple script to capture and upload images to Prusa Connect
"""
import time
import subprocess
import requests
import sys
import os
from pathlib import Path

# Load environment variables from .env file
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
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    env_vars[key.strip()] = value
    
    return env_vars

# Load configuration
env_vars = load_env()
PRUSA_TOKEN = env_vars.get('PRUSA_TOKEN', '')
PRINTER_FINGERPRINT = env_vars.get('PRINTER_FINGERPRINT', '')
CAMERA_NAME = env_vars.get('CAMERA_NAME', 'Raspberry Pi Camera')

# Settings
UPLOAD_INTERVAL = int(env_vars.get('UPLOAD_INTERVAL', '30'))  # seconds between uploads
IMAGE_PATH = "/tmp/prusa_snapshot.jpg"

# Detect which camera command to use
CAMERA_CMD = 'rpicam-still' if os.system('which rpicam-still > /dev/null 2>&1') == 0 else 'libcamera-still'

def capture_image():
    """Capture image from camera"""
    try:
        subprocess.run([
            CAMERA_CMD,
            '-o', IMAGE_PATH,
            '--width', '1920',
            '--height', '1080',
            '-t', '1',
            '-n'  # No preview
        ], check=True, capture_output=True, timeout=10)
        return True
    except Exception as e:
        print(f"Capture failed: {e}")
        return False

def set_camera_name():
    """Set camera name in Prusa Connect"""
    try:
        url = "https://connect.prusa3d.com/c/config"
        
        token = PRUSA_TOKEN.strip()
        
        headers = {
            'Content-Type': 'application/json',
            'Token': token
        }
        
        payload = {
            'config': {
                'name': CAMERA_NAME
            }
        }
        
        response = requests.put(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✓ Camera name set to: {CAMERA_NAME}")
            return True
        else:
            print(f"⚠ Failed to set camera name: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠ Could not set camera name: {e}")
        return False

def upload_to_prusa():
    """Upload image to Prusa Connect"""
    try:
        url = "https://connect.prusa3d.com/c/snapshot"
        
        # Clean token (remove any whitespace)
        token = PRUSA_TOKEN.strip()
        fingerprint = PRINTER_FINGERPRINT.strip() if PRINTER_FINGERPRINT else ""
        
        headers = {
            'Token': token,
        }
        
        # Only add fingerprint if it's not empty
        if fingerprint:
            headers['Fingerprint'] = fingerprint
        
        # DEBUG: Print what we're sending
        print(f"Token length: {len(token)} chars")
        if fingerprint:
            print(f"Fingerprint: {fingerprint}")
        
        # Read image data
        with open(IMAGE_PATH, 'rb') as f:
            image_data = f.read()
        
        # Upload as raw image data with proper content-type
        headers['Content-Type'] = 'image/jpg'
        response = requests.put(url, headers=headers, data=image_data, timeout=10)
        
        if response.status_code == 200:
            print(f"✓ Uploaded at {time.strftime('%H:%M:%S')}")
            return True
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return False

def main():
    print("Prusa Camera Uploader Starting...")
    print(f"Using camera command: {CAMERA_CMD}")
    print(f"Upload interval: {UPLOAD_INTERVAL} seconds")
    print("Press Ctrl+C to stop\n")
    
    # Check token is set
    if not PRUSA_TOKEN:
        print("ERROR: PRUSA_TOKEN not set!")
        print("Please create a .env file with your Prusa Connect token.")
        print("See .env.example for the template.")
        sys.exit(1)
    
    # Set camera name if configured
    if CAMERA_NAME:
        print(f"Setting camera name to: {CAMERA_NAME}")
        set_camera_name()
        print()
    
    while True:
        try:
            # Capture
            if capture_image():
                # Upload
                upload_to_prusa()
            
            # Wait
            time.sleep(UPLOAD_INTERVAL)
            
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()

