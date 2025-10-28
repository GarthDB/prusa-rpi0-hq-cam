# Prusa Camera Timelapse System

Professional timelapse photography system for Prusa MK4S 3D printer using Raspberry Pi Zero 2W and High Quality Camera, with GPIO trigger synchronization and Prusa Connect integration.

## Features

- ⚡ **Layer-synchronized timelapse** - Captures triggered by G-code at each layer change via GPIO
- ⏱️ **Time-based monitoring** - Continuous capture at configurable intervals
- 🌐 **Prusa Connect integration** - Live snapshot uploads during prints
- 🎥 **Automatic video compilation** - Converts images to MP4 after print completion
- 💾 **NAS upload support** - Automatic backup to network storage (SMB/NFS)
- 🎛️ **Highly configurable** - YAML-based configuration for all settings
- 🔄 **Auto-start service** - Runs automatically on boot via systemd
- 📊 **Comprehensive logging** - Detailed logs with rotation

## Hardware Requirements

### Required
- Prusa MK4S 3D Printer (or MK3.9/MK3.5 with xBuddy board)
- [GPIO Hackerboard](https://www.printedsolid.com/products/gpio-hackerboard-set) installed on printer
- Raspberry Pi Zero 2W
- Raspberry Pi High Quality Camera (12MP)
- CSI ribbon cable (included with camera)
- 2x female-to-female dupont jumper wires
- 5V 2A micro-USB power supply for Pi

### Optional
- 5V to micro-USB cable for powering Pi from printer (future enhancement)
- NAS or file server for video backup

## Quick Start

### 1. Hardware Setup

See [WIRING.md](WIRING.md) for detailed wiring instructions.

**Quick summary:**
- Connect HQ Camera to Pi via CSI cable
- Connect GPIO trigger: Hackerboard GPIO OUT → Pi GPIO17 (pin 11)
- Connect ground: Hackerboard GND → Pi GND (pin 6)
- Power Pi with separate 5V 2A supply

### 2. Software Installation

**On your Raspberry Pi Zero 2W:**

```bash
# Clone the repository
git clone https://github.com/GarthDB/prusa-rpi0-hq-cam.git
cd prusa-rpi0-hq-cam

# Run installation script
sudo ./install.sh
```

The installation script will:
- Update system packages
- Install required dependencies (libcamera, ffmpeg, Python packages)
- Create directory structure
- Install and configure systemd service
- Test camera functionality

### 3. Configuration

Edit the configuration file:

```bash
nano ~/prusa-camera/config.yaml
```

**Essential settings to update:**

1. **Prusa Connect Token** (for live monitoring)
   - Visit https://connect.prusa3d.com/
   - Navigate to "Cameras" section
   - Click "Add new other camera"
   - Copy the generated token
   - Paste into `prusa_connect.token` in config.yaml

2. **Camera Settings** (optional)
   - Adjust resolution, quality, rotation as needed
   - Default settings work well for most setups

3. **NAS Upload** (optional)
   - Enable and configure if you want automatic video backup
   - Supports SMB (Windows shares) and NFS

### 4. Enable and Start Service

```bash
# Enable service to start on boot
sudo systemctl enable prusa-camera

# Start service now
sudo systemctl start prusa-camera

# Check status
sudo systemctl status prusa-camera

# View logs
tail -f ~/prusa-camera/logs/camera.log
```

### 5. Configure PrusaSlicer

Add G-code commands to trigger captures:

**In PrusaSlicer → Printer Settings → Custom G-code:**

#### Layer Change G-code
Add this to trigger camera at end of each layer:

```gcode
; Trigger camera for timelapse
M42 P0 S255  ; Set GPIO OUT 0 HIGH
G4 P100      ; Wait 100ms
M42 P0 S0    ; Set GPIO OUT 0 LOW
```

#### End G-code
Add this at the very end of your existing end G-code:

```gcode
; Trigger video compilation
M118 A1 P0 action:compile_video
```

**Alternative method for end trigger:**
If the above doesn't work, you can manually trigger compilation via SSH:

```bash
python3 ~/prusa-camera/camera_service.py compile
```

## Usage

### During a Print

1. **Start your print** as normal from PrusaSlicer
2. **Monitor live** via Prusa Connect camera view (if configured)
3. **Check logs** if needed: `tail -f ~/prusa-camera/logs/camera.log`
4. **Images are captured** automatically at each layer change
5. **Video compiles** automatically when print completes

### After a Print

**Videos and images are stored in:**
```
~/prusa-camera/captures/YYYY-MM-DD/HHMMSS/
```

**Check video compilation log:**
```bash
tail ~/prusa-camera/logs/compile_video.log
```

**If NAS upload is enabled**, videos are automatically transferred and local copies are deleted (configurable).

### Manual Control

**Start/stop the service:**
```bash
sudo systemctl start prusa-camera
sudo systemctl stop prusa-camera
sudo systemctl restart prusa-camera
```

**Manually trigger compilation:**
```bash
python3 ~/prusa-camera/camera_service.py compile
```

**Test camera capture:**
```bash
libcamera-still -o test.jpg
```

## Configuration Reference

### Capture Modes

**Layer-based (synchronized):**
- Triggered by GPIO signal from printer
- Perfect timing - captures after print head moves away
- Best quality timelapses
- Requires G-code configuration

**Time-based (interval):**
- Captures every N seconds
- Good for monitoring
- Can run independently of printer
- Useful as fallback or for continuous monitoring

**Both modes can run simultaneously**

### Camera Settings

```yaml
camera:
  resolution: "max"        # or "1920x1080", "2592x1944", etc.
  quality: 85              # JPEG quality 0-100
  rotation: 0              # 0, 90, 180, 270
  hflip: false            # horizontal flip
  vflip: false            # vertical flip
  iso: "auto"             # or 100-800
  shutter_speed: "auto"   # or microseconds
  awb_mode: "auto"        # white balance mode
```

### Video Settings

```yaml
video:
  framerate: 30           # FPS for output video
  codec: "libx264"        # H.264 codec
  preset: "medium"        # encoding speed vs compression
  crf: 23                 # quality (lower = better, 18-28 recommended)
  output_resolution: "1920x1080"  # or "source"
```

### Storage Estimates

- **Per image**: ~4MB (12MP at quality 85)
- **200 layer print**: ~800MB
- **500 layer print**: ~2GB
- **Compiled video**: 20-50MB (30fps H.264)

**Recommended SD card**: 32GB or larger

## Troubleshooting

### Camera Not Detected

```bash
# Check if camera is detected
libcamera-hello --list-cameras

# If not detected, enable camera interface
sudo raspi-config
# → Interface Options → Camera → Enable
# Reboot after enabling

# Check CSI cable connections
```

### GPIO Triggers Not Working

```bash
# Test GPIO detection
python3 -c "
from gpiozero import Button
button = Button(17)
print('Monitoring GPIO17 for triggers...')
button.when_pressed = lambda: print('TRIGGER DETECTED!')
import time
while True:
    time.sleep(0.1)
"
# Then trigger from printer or manually short GPIO17 to 3.3V
```

**Check wiring:**
- Verify GPIO17 → Pin 11 on Pi
- Verify GND connection
- Check G-code is correct in PrusaSlicer

### Service Won't Start

```bash
# Check service status
sudo systemctl status prusa-camera

# View detailed logs
journalctl -u prusa-camera -f

# Check Python dependencies
pip3 list | grep -E 'gpiozero|PyYAML|requests|Pillow'

# Test script manually
python3 ~/prusa-camera/camera_service.py
```

### Video Compilation Fails

```bash
# Check compilation logs
tail ~/prusa-camera/logs/compile_video.log

# Verify ffmpeg is installed
ffmpeg -version

# Test manual compilation
~/prusa-camera/compile_video.sh ~/prusa-camera/captures/YYYY-MM-DD/HHMMSS
```

### Images But No Upload to Prusa Connect

- Verify token is correct in config.yaml
- Check internet connection on Pi
- Verify token hasn't expired (regenerate in Prusa Connect if needed)
- Check logs for error messages

### NAS Upload Fails

```bash
# Test SMB connection manually
smbclient //server/share -U username%password -c "ls"

# Test NFS mount manually
sudo mount -t nfs server:/export /tmp/test
ls /tmp/test
sudo umount /tmp/test
```

## Advanced Configuration

### Custom GPIO Pin

To use a different GPIO pin, edit `config.yaml`:

```yaml
gpio:
  trigger_pin: 17  # Change to your preferred pin (BCM numbering)
```

### Multiple Captures Per Layer

For extra smooth timelapses, trigger multiple times per layer:

```gcode
; In PrusaSlicer layer change G-code
M42 P0 S255
G4 P100
M42 P0 S0
G4 P500        ; Wait 500ms
M42 P0 S255    ; Capture again
G4 P100
M42 P0 S0
```

### Custom Video Settings

For 4K output:
```yaml
video:
  output_resolution: "3840x2160"
  crf: 20  # Higher quality for 4K
  preset: "slow"  # Better compression
```

For faster encoding (lower quality):
```yaml
video:
  preset: "fast"
  crf: 28
```

## Project Structure

```
prusa-rpi0-hq-cam/
├── camera_service.py      # Main camera service daemon
├── compile_video.sh       # Video compilation script
├── config.yaml           # Configuration file
├── requirements.txt      # Python dependencies
├── camera.service        # Systemd service definition
├── install.sh           # Automated installation script
├── README.md            # This file
└── WIRING.md           # Detailed wiring guide
```

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Future Enhancements

- [ ] Power Pi from printer's 5V supply
- [ ] Web interface for configuration
- [ ] Real-time streaming support
- [ ] Print progress overlay on images
- [ ] Integration with OctoPrint/Mainsail
- [ ] Support for multiple cameras
- [ ] Advanced motion detection
- [ ] Cloud upload options (Dropbox, Google Drive, etc.)

## License

MIT License - feel free to use and modify as needed.

## Credits

Created for the Prusa MK4S community. Inspired by the need for better timelapse solutions with GPIO synchronization.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the [WIRING.md](WIRING.md) guide for hardware setup
- Review logs in `~/prusa-camera/logs/`

## Acknowledgments

- Prusa Research for the MK4S and GPIO Hackerboard
- Raspberry Pi Foundation for the excellent HQ Camera
- The 3D printing and maker community

---

**Happy printing and capturing!** 📷🖨️

