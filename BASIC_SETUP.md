# Basic Setup Guide - Raspberry Pi Camera to Prusa Connect

Start here! This guide walks you through setting up your Raspberry Pi Zero 2W and HQ Camera to upload images to Prusa Connect. Once this is working, you can add the GPIO timelapse features later.

## What You'll Need

### Required Hardware
- ✅ Raspberry Pi Zero 2W
- ✅ Raspberry Pi High Quality Camera (12MP)
- ✅ CSI ribbon cable (included with camera)
- ✅ MicroSD card (16GB minimum, 32GB recommended)
- ✅ 5V 2A micro-USB power supply
- ✅ Computer with SD card reader
- ✅ WiFi network credentials

### Setup Method
This guide uses **headless setup** - no monitor, keyboard, or HDMI cable needed! Everything is configured through the Raspberry Pi Imager before first boot, then accessed via SSH over WiFi.

---

## Step 1: Prepare the SD Card

### 1.1 Download Raspberry Pi Imager

Download from: https://www.raspberrypi.com/software/

Available for Windows, Mac, and Linux.

### 1.2 Write Raspberry Pi OS

1. **Insert SD card** into your computer
2. **Open Raspberry Pi Imager**
3. **Choose Device:** Raspberry Pi Zero 2 W
4. **Choose OS:** 
   - Raspberry Pi OS (64-bit)
   - Or "Raspberry Pi OS Lite (64-bit)" if you want minimal install
   - Recommended: Regular "Raspberry Pi OS (64-bit)" for easier setup
5. **Choose Storage:** Select your SD card
6. **Click ⚙️ (Settings gear)** before writing!

### 1.3 Configure Advanced Options (CRITICAL for Headless Setup!)

**This step is what makes headless setup work** - you're configuring WiFi and SSH before the Pi ever boots, so you can access it remotely without needing a monitor or keyboard.

In the settings window, configure:

**General Tab:**
- ✅ **Set hostname:** `prusa-camera` (or whatever you prefer)
- ✅ **Set username and password:**
  - Username: `pi` (or your choice)
  - Password: (choose a secure password - you'll need this!)
- ✅ **Configure wireless LAN:**
  - SSID: Your WiFi network name
  - Password: Your WiFi password
  - Wireless LAN country: Your country code (e.g., US, GB, DE)
- ✅ **Set locale settings:**
  - Time zone: Your timezone
  - Keyboard layout: Your keyboard layout

**Services Tab:**
- ✅ **Enable SSH:** Check "Use password authentication"
  - **This is critical!** Without SSH enabled, you can't access the Pi headlessly

Click **Save**, then click **Yes** to write to SD card.

**What just happened?**
You configured the Pi to:
- Connect to your WiFi automatically on first boot
- Enable SSH so you can access it remotely
- Set hostname so you can find it easily
- All without ever needing a monitor!

⏱️ Writing takes 5-10 minutes.

---

## Step 2: Boot the Raspberry Pi (Headless!)

### 2.1 Insert SD Card and Power On

**No monitor or keyboard needed!** Just:

1. **Eject SD card** from computer
2. **Insert SD card** into Raspberry Pi (slot on underside)
3. **Connect power** via micro-USB port (the one labeled "PWR IN")
4. **Wait 1-2 minutes** for first boot

**What's happening (you can't see it, but it's working!):**
- Resizing the filesystem to use full SD card
- Connecting to your WiFi network
- Starting SSH server
- Setting hostname
- Rebooting automatically

**Green LED activity:** Should blink irregularly as it boots (this is normal)

### 2.2 Find Your Pi on the Network

**Since we're doing headless setup, you need to find the Pi on your network.** Here are three methods:

**Method 1: Using hostname (easiest)**
```bash
# From your computer, try to ping
ping prusa-camera.local
```

If that works, your Pi's address is `prusa-camera.local`

**Method 2: Check your router**
- Log into your router's admin page
- Look for new device named "prusa-camera" or "raspberrypi"
- Note its IP address (e.g., 192.168.1.50)

**Method 3: Network scanner**
- Use app like "Fing" (iOS/Android) or "Angry IP Scanner" (desktop)
- Scan your network for new Raspberry Pi devices

### 2.3 Connect via SSH (Your First Access!)

**This is it - connecting to your Pi without any monitor!**

From your computer's terminal/command prompt:

```bash
# Using hostname (easier)
ssh pi@prusa-camera.local

# Or using IP address
ssh pi@192.168.1.50
```

Enter the password you set in Step 1.3.

**First time connecting?**
- You'll see a message about RSA key fingerprint
- Type `yes` and press Enter

---

## Step 3: Connect the HQ Camera

### 3.1 Power Off the Pi

```bash
sudo shutdown -h now
```

Wait 30 seconds, then unplug power.

### 3.2 Attach the Camera

1. **Locate the CSI port** on Raspberry Pi Zero 2W
   - It's between the USB ports and HDMI port
   - Has a small black plastic clip

2. **Open the CSI connector**
   - Gently pull UP on the black plastic clip
   - It should lift about 2mm
   - Don't force it!

3. **Insert the ribbon cable**
   - Use the cable that came with HQ Camera (usually 15cm)
   - **Important:** Insert with contacts facing TOWARDS the USB ports
   - Slide it in firmly until it won't go further

4. **Close the connector**
   - Push the black clip DOWN to lock the cable
   - It should click into place

5. **Connect cable to camera**
   - On the HQ Camera, open the CSI connector (pull up)
   - Insert cable with contacts facing TOWARDS the camera PCB
   - Close connector (push down)

6. **Mount the camera**
   - Point camera towards your printer
   - Use camera mount or tripod
   - Make sure ribbon cable has slack (not stretched tight)

### 3.3 Power On and Test

1. **Plug in power** to Pi
2. **Wait 30 seconds** for boot
3. **SSH back in:**
   ```bash
   ssh pi@prusa-camera.local
   ```

4. **Install camera software:**
   ```bash
   # Update package list
   sudo apt update
   
   # Install libcamera apps
   sudo apt install -y libcamera-apps
   ```
   
   This takes 1-2 minutes.

5. **Check if camera is detected:**
   ```bash
   libcamera-hello --list-cameras
   ```

   **Expected output:**
   ```
   Available cameras
   -----------------
   0 : imx477 [4056x3040] (/base/soc/i2c0mux/i2c@1/imx477@1a)
       Modes: 'SRGGB10_CSI2P' : 1332x990 [120.05 fps - ...]
              'SRGGB12_CSI2P' : 2028x1080 [50.03 fps - ...]
                                2028x1520 [40.01 fps - ...]
                                4056x3040 [10.00 fps - ...]
   ```

   If you see this, **camera is working!** ✅

6. **Capture a test image:**
   ```bash
   libcamera-still -o test.jpg
   ```

   This captures a 2-second preview, then saves `test.jpg`.

7. **View the image** (optional):
   - Use SCP to copy to your computer:
     ```bash
     # From your computer
     scp pi@prusa-camera.local:~/test.jpg .
     ```
   - Or use FileZilla/WinSCP to browse Pi files

**Troubleshooting:**
- **"Camera not detected"** → Check cable connections, try reboot
- **Purple/wrong colors** → Cable backwards, reverse it
- **Error about vcgencmd** → Update system (see below)

---

## Step 4: Update System and Install Software

### 4.1 Update Everything

```bash
# Update package list
sudo apt update

# Upgrade all packages (takes 5-15 minutes)
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-yaml git
```

### 4.2 Reboot

```bash
sudo reboot
```

Wait 30 seconds, then SSH back in.

---

## Step 5: Set Up Prusa Connect

### 5.1 Get Your Camera Token

1. **Go to Prusa Connect:** https://connect.prusa3d.com/
2. **Log in** with your Prusa account
3. **Click "Cameras"** in the left sidebar
4. **Click "Add new other camera"**
5. **Copy the Token** that appears (long string like `abc123def456...`)
6. **Keep this browser tab open** - you'll need it to verify images

### 5.2 Create Upload Script

On the Pi, create a simple upload script:

```bash
# Create directory
mkdir -p ~/prusa-camera
cd ~/prusa-camera

# Create the script
nano upload_to_prusa.py
```

Paste this code:

```python
#!/usr/bin/env python3
"""
Simple script to capture and upload images to Prusa Connect
"""
import time
import subprocess
import requests
import sys

# EDIT THIS: Paste your Prusa Connect token here
PRUSA_TOKEN = "YOUR_TOKEN_HERE"
PRINTER_FINGERPRINT = ""  # Optional, can be blank

# Settings
UPLOAD_INTERVAL = 30  # seconds between uploads
IMAGE_PATH = "/tmp/prusa_snapshot.jpg"

def capture_image():
    """Capture image from camera"""
    try:
        subprocess.run([
            'libcamera-still',
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

def upload_to_prusa():
    """Upload image to Prusa Connect"""
    try:
        url = "https://connect.prusa3d.com/c/snapshot"
        headers = {
            'Token': PRUSA_TOKEN,
            'Fingerprint': PRINTER_FINGERPRINT
        }
        
        with open(IMAGE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.put(url, headers=headers, files=files, timeout=10)
        
        if response.status_code == 200:
            print(f"✓ Uploaded at {time.strftime('%H:%M:%S')}")
            return True
        else:
            print(f"✗ Upload failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return False

def main():
    print("Prusa Camera Uploader Starting...")
    print(f"Upload interval: {UPLOAD_INTERVAL} seconds")
    print("Press Ctrl+C to stop\n")
    
    # Check token is set
    if PRUSA_TOKEN == "YOUR_TOKEN_HERE":
        print("ERROR: Please edit the script and set your Prusa Connect token!")
        sys.exit(1)
    
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
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

### 5.3 Edit the Token

```bash
nano upload_to_prusa.py
```

Find this line:
```python
PRUSA_TOKEN = "YOUR_TOKEN_HERE"
```

Replace `YOUR_TOKEN_HERE` with your actual token from Step 5.1.

**Save:** `Ctrl+X`, `Y`, `Enter`

### 5.4 Install Python Dependencies

```bash
pip3 install requests
```

### 5.5 Make Script Executable

```bash
chmod +x upload_to_prusa.py
```

---

## Step 6: Test the Basic Setup

### 6.1 Run the Upload Script

```bash
python3 ~/prusa-camera/upload_to_prusa.py
```

You should see:
```
Prusa Camera Uploader Starting...
Upload interval: 30 seconds
Press Ctrl+C to stop

✓ Uploaded at 14:23:45
✓ Uploaded at 14:24:15
✓ Uploaded at 14:24:45
```

### 6.2 Check Prusa Connect

1. **Go back to Prusa Connect** in your browser
2. **Go to Cameras section**
3. **You should see live images** from your camera updating every 30 seconds!

**Success!** 🎉 Your basic setup is working!

Press `Ctrl+C` to stop the script.

---

## Step 7: Make It Run Automatically

### 7.1 Create Systemd Service

```bash
sudo nano /etc/systemd/system/prusa-camera.service
```

Paste this:

```ini
[Unit]
Description=Prusa Camera Upload Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/prusa-camera
ExecStart=/usr/bin/python3 /home/pi/prusa-camera/upload_to_prusa.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save:** `Ctrl+X`, `Y`, `Enter`

### 7.2 Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable prusa-camera

# Start service now
sudo systemctl start prusa-camera

# Check status
sudo systemctl status prusa-camera
```

You should see "active (running)" in green.

### 7.3 View Logs

```bash
# Follow live logs
sudo journalctl -u prusa-camera -f

# Press Ctrl+C to exit
```

---

## You're Done with Basic Setup! ✅

Your Raspberry Pi is now:
- ✅ Capturing images from HQ Camera
- ✅ Uploading to Prusa Connect every 30 seconds
- ✅ Running automatically on boot
- ✅ Ready to monitor your prints remotely!

---

## Next Steps

### Position Your Camera

- Mount camera to get good view of print bed
- Adjust focus by rotating lens on HQ Camera
- Use test images to verify framing

### Adjust Upload Interval

Edit the script:
```bash
nano ~/prusa-camera/upload_to_prusa.py
```

Change:
```python
UPLOAD_INTERVAL = 30  # Change this number (seconds)
```

Restart service:
```bash
sudo systemctl restart prusa-camera
```

### Add GPIO Timelapse Features

Once basic setup is working, you can add the advanced features:

1. **Read [WIRING.md](WIRING.md)** - Connect GPIO trigger from hackerboard
2. **Run full installation:**
   ```bash
   cd ~/prusa-camera
   git clone https://github.com/GarthDB/prusa-rpi0-hq-cam.git full-system
   cd full-system
   sudo ./install.sh
   ```
3. **Configure layer-based triggers** using [GCODE_EXAMPLES.md](GCODE_EXAMPLES.md)

---

## Troubleshooting

### Camera Not Detected After Reboot

```bash
# Check camera is enabled
sudo raspi-config
# → Interface Options → Legacy Camera → Disable (we want NEW camera system)

# Reboot
sudo reboot
```

### Upload Fails: "Connection Error"

- Check WiFi is connected: `ping google.com`
- Verify token is correct in script
- Check Prusa Connect website is accessible

### Service Won't Start

```bash
# Check logs for errors
sudo journalctl -u prusa-camera -n 50

# Test script manually
python3 ~/prusa-camera/upload_to_prusa.py

# Check permissions
ls -l ~/prusa-camera/upload_to_prusa.py
```

### Images Are Dark/Overexposed

Edit script, add camera settings after line with `libcamera-still`:

```python
subprocess.run([
    'libcamera-still',
    '-o', IMAGE_PATH,
    '--width', '1920',
    '--height', '1080',
    '-t', '1',
    '-n',
    '--brightness', '0.1',  # Add this (-1.0 to 1.0)
    '--contrast', '1.1',     # Add this (0 to 2.0)
    '--awb', 'auto'          # Auto white balance
], check=True, capture_output=True, timeout=10)
```

Restart service after editing.

### Check System Resources

```bash
# Check temperature
vcgencmd measure_temp

# Check memory
free -h

# Check disk space
df -h
```

Pi Zero 2W can get warm - ensure good ventilation!

---

## Quick Command Reference

```bash
# View camera service status
sudo systemctl status prusa-camera

# Stop camera service
sudo systemctl stop prusa-camera

# Start camera service
sudo systemctl start prusa-camera

# Restart camera service
sudo systemctl restart prusa-camera

# View live logs
sudo journalctl -u prusa-camera -f

# Capture test image
libcamera-still -o test.jpg

# Check WiFi connection
ip addr show wlan0

# Reboot Pi
sudo reboot

# Shutdown Pi
sudo shutdown -h now
```

---

## Support

Having issues? Check:
1. Camera is firmly connected (both ends of ribbon cable)
2. WiFi is working (`ping google.com`)
3. Token is correct in script
4. Service is running (`systemctl status prusa-camera`)
5. No errors in logs (`journalctl -u prusa-camera`)

For advanced features and GPIO timelapse, see the full [README.md](README.md)!

