# Wiring Guide

Complete wiring guide for connecting your Raspberry Pi Zero 2W and HQ Camera to the Prusa MK4S GPIO Hackerboard.

## Required Hardware

### What You Already Have
- ✅ Prusa MK4S 3D Printer
- ✅ GPIO Hackerboard (installed on MK4S)
- ✅ Raspberry Pi Zero 2W
- ✅ Raspberry Pi High Quality Camera (12MP)
- ✅ CSI Ribbon Cable (included with HQ Camera)

### What You Need to Purchase

#### Essential Components
1. **Female-to-Female Dupont Jumper Wires** (2 minimum)
   - Length: 10-20cm (4-8 inches)
   - Gauge: 22-26 AWG
   - Purpose: Connect hackerboard GPIO to Raspberry Pi GPIO
   - Where to buy: Amazon, Adafruit, SparkFun, local electronics store
   - Cost: ~$5-10 for a pack
   - Search terms: "dupont jumper wires female to female"

#### Optional for Power Integration (Future)
2. **5V to Micro-USB Power Cable/Adapter**
   - Purpose: Power Pi from printer's 5V supply
   - Only needed if you want to power Pi from printer
   - Alternative: Use a separate USB power supply (recommended for initial setup)

#### For Initial Testing (Recommended)
3. **5V 2A Micro-USB Power Supply**
   - Purpose: Independent power for Raspberry Pi
   - Most phone chargers work (micro-USB, not USB-C)
   - You may already have one

## Connection Diagram

```
┌─────────────────────────────────────────┐
│         Prusa MK4S with MK4             │
│                                         │
│  ┌──────────────────────────────┐      │
│  │   GPIO Hackerboard           │      │
│  │                               │      │
│  │  [GPIO OUT] ──────┐          │      │
│  │                   │           │      │
│  │      [GND] ───────┼──────┐   │      │
│  └───────────────────┼──────┼───┘      │
│                      │      │           │
└──────────────────────┼──────┼───────────┘
                       │      │
                Female-Female Dupont Wires
                       │      │
┌──────────────────────┼──────┼───────────┐
│  Raspberry Pi Zero 2W│      │           │
│                      │      │           │
│  ┌────────────────┐ │      │           │
│  │  GPIO Header   │ │      │           │
│  │                │ │      │           │
│  │ Pin 11 (GPIO17)├─┘      │           │
│  │                │        │           │
│  │ Pin 6  (GND)   ├────────┘           │
│  │                │                    │
│  └────────────────┘                    │
│         │                              │
│    CSI Port                            │
│         │                              │
│         └────────────────┐             │
│                          │             │
└──────────────────────────┼─────────────┘
                           │
                    CSI Ribbon Cable
                           │
              ┌────────────┴──────────┐
              │   Raspberry Pi HQ     │
              │   Camera (12MP)       │
              └───────────────────────┘
```

## Step-by-Step Wiring Instructions

### Step 1: Connect HQ Camera to Raspberry Pi

1. **Locate the CSI port** on your Raspberry Pi Zero 2W
   - It's the wide, flat connector between the USB ports and HDMI port
   - Has a black plastic clip that pulls up

2. **Prepare the ribbon cable**
   - Use the 15cm CSI cable included with the HQ Camera
   - Note which side has the blue backing tape (contacts face opposite)

3. **Insert the cable into Pi**
   - Gently pull up the black plastic clip on the CSI port
   - Insert ribbon cable with contacts facing TOWARDS the USB ports
   - Push the clip back down to secure

4. **Connect to camera**
   - On the camera module, pull up the CSI connector clip
   - Insert cable with contacts facing TOWARDS the camera PCB
   - Push clip down to secure

5. **Test connection**
   - Cable should be snug and secure
   - No visible metal contacts should be showing outside the connector

### Step 2: GPIO Trigger Connection (Hackerboard to Pi)

#### Understanding the Connections

**Raspberry Pi Zero 2W GPIO Pinout (40-pin header):**
```
     3V3  (1) (2)  5V
   GPIO2  (3) (4)  5V
   GPIO3  (5) (6)  GND  ← Use this for GND
   GPIO4  (7) (8)  GPIO14
     GND  (9) (10) GPIO15
GPIO17 (11) (12) GPIO18  ← Use Pin 11 for trigger
     ...
```

#### Wiring Steps

1. **Identify hackerboard GPIO pins**
   - Check your hackerboard documentation for GPIO output pins
   - Typically labeled as "GPIO OUT" or "OUT 0", "OUT 1", etc.
   - Also locate a GND (ground) pin

2. **Connect trigger signal (Wire #1)**
   - **From:** Hackerboard GPIO output pin (typically OUT 0)
   - **To:** Raspberry Pi GPIO17 (Physical Pin 11)
   - **Color suggestion:** Use a colored wire (red, yellow, or white)

3. **Connect ground (Wire #2)**
   - **From:** Hackerboard GND pin
   - **To:** Raspberry Pi GND (Physical Pin 6 or Pin 9)
   - **Color suggestion:** Use black wire for ground

4. **Verify connections**
   - Wires should be firmly seated in the GPIO headers
   - No loose connections
   - Double-check pin numbers

### Step 3: Power Connection (Initial Setup)

For initial testing and setup:

1. **Use separate power supply**
   - Connect 5V 2A micro-USB power supply to Pi's power port
   - This is the safer option for testing

2. **Power on sequence**
   - Power on Raspberry Pi first
   - Then power on the printer
   - This prevents any power surges

## GPIO Hackerboard Pin Reference

The GPIO Hackerboard on your Prusa MK4S provides the following connections:

### Typical Pinout (verify with your specific board)
- **GPIO OUT 0**: First output pin (use this for camera trigger)
- **GPIO OUT 1-3**: Additional outputs (for future expansion)
- **GND**: Ground pin (multiple available)
- **5V**: 5V output (for future power integration)
- **3.3V**: 3.3V output (not needed for this project)

### G-code Control
The hackerboard GPIO pins are controlled via G-code commands:
- `M42 P0 S255` - Set GPIO OUT 0 to HIGH
- `M42 P0 S0` - Set GPIO OUT 0 to LOW

## Future: Powering Pi from Printer

⚠️ **Not required for initial setup** - use separate power supply first!

Once your system is working, you can optionally power the Pi from the printer:

### Option A: Use xBuddy USB Port
1. Some xBuddy boards have a USB port that provides 5V
2. Use a micro-USB cable from this port to the Pi
3. Verify voltage output is stable 5V
4. Check current capability (Pi + Camera need ~1.5A)

### Option B: Wire from Printer PSU
1. Requires electrical knowledge - only attempt if comfortable
2. Need 5V voltage regulator or step-down converter
3. Tap into printer's 24V PSU and regulate to 5V
4. Use appropriate gauge wire (18-20 AWG for power)
5. Add proper fusing for safety

⚠️ **Warning:** Incorrect power wiring can damage your printer and/or Pi. Use separate power supply unless you're experienced with electronics.

## Testing Your Connections

### Test 1: Camera Detection
```bash
libcamera-hello --list-cameras
```
Should show your HQ Camera detected.

### Test 2: Capture Test Image
```bash
libcamera-still -o test.jpg
```
Should capture an image to test.jpg.

### Test 3: GPIO Trigger Detection
```bash
# Monitor GPIO17 for triggers
python3 -c "
from gpiozero import Button
button = Button(17)
print('Waiting for trigger on GPIO17...')
button.when_pressed = lambda: print('Trigger detected!')
while True:
    pass
"
```
Then trigger the hackerboard from printer (or manually), should see "Trigger detected!"

## Troubleshooting

### Camera Not Detected
- Check CSI cable connections on both ends
- Try `sudo raspi-config` → Interface Options → Camera → Enable
- Reboot after enabling camera
- Try a different CSI cable if available

### GPIO Trigger Not Working
- Verify correct pin numbers (BCM vs. physical numbering)
- Check wire connections are secure
- Test with multimeter: should see ~3.3V when triggered
- Verify hackerboard is functioning (test with LED)

### Power Issues
- Pi not booting: Insufficient power supply (<2A)
- Random reboots: Power supply instability
- Camera failing: Power supply can't handle load
- Solution: Use quality 2A+ power supply

## Safety Notes

1. **Power Off First**: Always power off printer and Pi before connecting/disconnecting wires
2. **Check Polarity**: Double-check GND connections
3. **Avoid Shorts**: Keep wires away from metal parts of printer
4. **Secure Wires**: Use zip ties or clips to prevent wires from interfering with printer movement
5. **Strain Relief**: Leave slack in wires to prevent pulling on connections

## Shopping List Summary

| Item | Quantity | Est. Cost | Priority |
|------|----------|-----------|----------|
| Female-Female Dupont Wires | 2 (buy pack of 40) | $5-10 | **Required** |
| 5V 2A Micro-USB Power Supply | 1 | $8-15 | **Required*** |
| Raspberry Pi Zero 2W | 1 | $15 | Already have ✓ |
| Raspberry Pi HQ Camera | 1 | $50 | Already have ✓ |
| GPIO Hackerboard | 1 | $16 | Already have ✓ |

\* If you don't already have a compatible phone charger

**Total additional cost: ~$5-25**

## Next Steps

Once wiring is complete:
1. Proceed to software installation (see README.md)
2. Configure Prusa Connect token
3. Add G-code commands to PrusaSlicer
4. Test the system!

