# G-code Examples for PrusaSlicer

This document provides G-code snippets to add to PrusaSlicer for triggering the camera timelapse system.

## Quick Reference

### Layer Change G-code (Camera Trigger)

Add this to **Printer Settings → Custom G-code → After layer change G-code**:

```gcode
; === Prusa Camera Timelapse Trigger ===
M42 P0 S255  ; Set GPIO OUT 0 HIGH (trigger camera)
G4 P100      ; Wait 100ms (debounce)
M42 P0 S0    ; Set GPIO OUT 0 LOW (reset)
```

### End Print G-code (Video Compilation)

Add this to **Printer Settings → Custom G-code → End G-code** (at the very end):

```gcode
; === Trigger Video Compilation ===
M118 A1 P0 action:compile_video
```

## Detailed Examples

### Basic Layer Trigger

The simplest setup - triggers once per layer:

```gcode
; Trigger camera
M42 P0 S255
G4 P100
M42 P0 S0
```

### Layer Trigger with Stabilization Delay

If your printer vibrates after moves, add a longer delay before trigger:

```gcode
; Wait for printer to stabilize
G4 P500

; Trigger camera
M42 P0 S255
G4 P100
M42 P0 S0
```

### Multiple Captures Per Layer

For smoother timelapses, capture multiple times per layer:

```gcode
; First capture
M42 P0 S255
G4 P100
M42 P0 S0

; Wait between captures
G4 P1000

; Second capture
M42 P0 S255
G4 P100
M42 P0 S0
```

### Layer Trigger with LED Indicator

If you have an LED connected to another GPIO pin:

```gcode
; Turn on LED
M42 P1 S255

; Wait for stabilization
G4 P500

; Trigger camera
M42 P0 S255
G4 P100
M42 P0 S0

; Turn off LED
G4 P200
M42 P1 S0
```

## Complete PrusaSlicer Configuration Example

Here's a complete example showing where to place each code block:

### Printer Settings → Custom G-code

#### Start G-code
Your existing start G-code + optional initial trigger:

```gcode
; ... your existing start G-code ...

; Optional: Capture initial state
M42 P0 S255
G4 P100
M42 P0 S0
```

#### After layer change G-code

```gcode
; Prusa Camera Timelapse
G4 P500      ; Stabilization delay (adjust as needed)
M42 P0 S255  ; Trigger HIGH
G4 P100      ; Debounce
M42 P0 S0    ; Trigger LOW
```

#### End G-code
Your existing end G-code + video compilation trigger:

```gcode
; ... your existing end G-code (park, cool down, etc.) ...

; Compile timelapse video
M118 A1 P0 action:compile_video
```

## GPIO Pin Reference

The GPIO Hackerboard pins are controlled by `M42` command:

- `M42 P0` - GPIO OUT 0 (use for camera trigger)
- `M42 P1` - GPIO OUT 1 (available for other uses)
- `M42 P2` - GPIO OUT 2 (available for other uses)
- `M42 P3` - GPIO OUT 3 (available for other uses)

**Syntax:**
- `M42 Pn S255` - Set pin HIGH (3.3V output)
- `M42 Pn S0` - Set pin LOW (0V output)

## Troubleshooting G-code

### Test Individual Components

#### Test GPIO Trigger Only

Send via OctoPrint/Pronterface console:

```gcode
M42 P0 S255
G4 P100
M42 P0 S0
```

Watch camera service logs to confirm trigger detection.

#### Test Video Compilation Trigger

```gcode
M118 A1 P0 action:compile_video
```

Or manually via SSH:
```bash
python3 ~/prusa-camera/camera_service.py compile
```

### Verify GPIO Pin Mapping

If triggers aren't working, verify your hackerboard pin mapping:

```gcode
; Try different pins
M42 P0 S255
M42 P1 S255
M42 P2 S255
M42 P3 S255
```

Use a multimeter or LED to identify which physical pin corresponds to P0.

## Advanced Configurations

### Conditional Triggering

Only trigger camera above certain layer height:

```gcode
; Only trigger above layer 10
{if layer_num > 10}
M42 P0 S255
G4 P100
M42 P0 S0
{endif}
```

### Print Progress Indicator

Flash LED based on print progress:

```gcode
; Flash LED at 25%, 50%, 75%, 100%
{if layer_z > 0.25 * print_height}
M42 P1 S255
G4 P500
M42 P1 S0
{endif}
```

### Time-based Capture Override

Switch to time-based capture for specific layers:

```gcode
; For first 10 layers, capture every layer
{if layer_num <= 10}
M42 P0 S255
G4 P100
M42 P0 S0
; After that, time-based mode handles it
{endif}
```

## Alternative: Manual Video Compilation

If `M118` action command doesn't work with your setup, you can manually trigger compilation:

### Option 1: SSH into Pi after print
```bash
ssh pi@raspberrypi.local
python3 ~/prusa-camera/camera_service.py compile
```

### Option 2: Add cron job to auto-detect completed prints
```bash
# Edit crontab
crontab -e

# Add this line to check every 5 minutes
*/5 * * * * python3 ~/prusa-camera/check_and_compile.py
```

### Option 3: Use G-code to create trigger file
```gcode
; In End G-code
M28 /usb/trigger_compile.txt
compile
M29
```

Then have a script watch for this file on the USB drive.

## PrusaSlicer Variables

You can use PrusaSlicer variables in your G-code:

```gcode
; Add print info to console
M118 Print: {input_filename}
M118 Layer: {layer_num}/{total_layer_count}
M118 Height: {layer_z}mm

; Trigger camera
M42 P0 S255
G4 P100
M42 P0 S0
```

Available variables:
- `{layer_num}` - Current layer number
- `{layer_z}` - Current Z height
- `{total_layer_count}` - Total layers in print
- `{input_filename}` - Name of the G-code file
- `{print_time}` - Estimated print time

## Testing Checklist

Before starting a real print, test:

- [ ] Single layer trigger works
- [ ] Camera captures on trigger
- [ ] Images saved to correct directory
- [ ] Multiple triggers work (won't crash printer)
- [ ] End G-code triggers compilation
- [ ] Video compiles successfully
- [ ] NAS upload works (if configured)

## Resources

- [Prusa G-code Reference](https://help.prusa3d.com/article/prusa-firmware-specific-g-code-commands_112173)
- [M42 Command Documentation](https://reprap.org/wiki/G-code#M42:_Switch_I.2FO_pin)
- [PrusaSlicer Variables](https://help.prusa3d.com/article/placeholder-parser_205643)

## Support

If you have issues with G-code:
1. Check printer firmware version (GPIO support added in specific versions)
2. Verify hackerboard is properly installed and detected
3. Test with LED before camera connection
4. Check printer console for error messages
5. Review camera service logs for trigger detection

---

**Pro Tip:** Start with the basic layer trigger, verify it works, then add enhancements like stabilization delays and multiple captures.

