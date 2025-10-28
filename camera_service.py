#!/usr/bin/env python3
"""
Prusa Camera Timelapse Service

Main service for capturing images from Raspberry Pi HQ Camera,
triggered by GPIO signals from Prusa MK4S hackerboard or time intervals.
Uploads snapshots to Prusa Connect for live monitoring.

Author: Generated for Prusa MK4S Camera Setup
License: MIT
"""

import os
import sys
import time
import signal
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import subprocess
import json

import yaml
import requests
from gpiozero import Button
from PIL import Image
import psutil


class CameraService:
    """Main camera service class."""
    
    def __init__(self, config_path: str = "/home/pi/prusa-camera/config.yaml"):
        """Initialize the camera service."""
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.running = False
        self.print_active = False
        self.capture_counter = 0
        self.current_session_dir: Optional[Path] = None
        self.last_upload_time = 0
        self.logger = self._setup_logging()
        
        # Load configuration
        self.load_config()
        
        # Setup GPIO trigger
        self.trigger_button: Optional[Button] = None
        self._setup_gpio()
        
        # Setup time-based capture thread
        self.time_capture_thread: Optional[threading.Thread] = None
        
        # Warmup camera
        self._warmup_camera()
        
        self.logger.info("Camera service initialized successfully")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("PrusaCamera")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("/home/pi/prusa-camera/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_dir / "camera.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"Configuration loaded from {self.config_path}")
            
            # Update logging level if specified
            if 'logging' in self.config:
                level = getattr(logging, self.config['logging'].get('level', 'INFO'))
                self.logger.setLevel(level)
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def _setup_gpio(self) -> None:
        """Setup GPIO pin for trigger detection."""
        try:
            gpio_config = self.config.get('gpio', {})
            pin = gpio_config.get('trigger_pin', 17)
            pull = gpio_config.get('trigger_pull', 'down')
            bounce_time = gpio_config.get('debounce_ms', 100) / 1000.0
            
            # Map pull configuration
            pull_up = pull.lower() == 'up'
            
            self.trigger_button = Button(
                pin,
                pull_up=pull_up,
                bounce_time=bounce_time
            )
            
            # Attach handler based on edge configuration
            edge = gpio_config.get('trigger_edge', 'rising')
            if edge == 'rising':
                self.trigger_button.when_pressed = self._on_gpio_trigger
            elif edge == 'falling':
                self.trigger_button.when_released = self._on_gpio_trigger
            else:  # both
                self.trigger_button.when_pressed = self._on_gpio_trigger
                self.trigger_button.when_released = self._on_gpio_trigger
            
            self.logger.info(f"GPIO trigger configured on pin {pin}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup GPIO: {e}")
            self.logger.warning("Layer-based capture will not be available")
    
    def _warmup_camera(self) -> None:
        """Perform warmup captures to let camera adjust."""
        warmup_count = self.config.get('advanced', {}).get('warmup_captures', 2)
        self.logger.info(f"Warming up camera with {warmup_count} captures...")
        
        for i in range(warmup_count):
            try:
                # Quick low-res capture for warmup
                subprocess.run(
                    ['libcamera-still', '-o', '/tmp/warmup.jpg', '-t', '1', 
                     '--width', '640', '--height', '480', '-n'],
                    check=True,
                    capture_output=True
                )
                time.sleep(0.5)
            except Exception as e:
                self.logger.warning(f"Warmup capture {i+1} failed: {e}")
        
        # Clean up warmup file
        try:
            os.remove('/tmp/warmup.jpg')
        except:
            pass
        
        self.logger.info("Camera warmup complete")
    
    def _on_gpio_trigger(self) -> None:
        """Handle GPIO trigger event."""
        self.logger.debug("GPIO trigger detected")
        
        if not self.config.get('capture', {}).get('layer_mode', {}).get('enabled', True):
            self.logger.debug("Layer mode disabled, ignoring trigger")
            return
        
        # Start print session if not already active
        if not self.print_active:
            self.logger.info("Print session started (first layer trigger)")
            self._start_print_session()
        
        # Delay before capture if configured
        delay = self.config.get('capture', {}).get('layer_mode', {}).get('capture_delay', 0.5)
        if delay > 0:
            time.sleep(delay)
        
        # Capture image
        self._capture_image("layer")
    
    def _start_print_session(self) -> None:
        """Start a new print session."""
        self.print_active = True
        self.capture_counter = 0
        
        # Create session directory
        base_dir = Path(self.config.get('storage', {}).get('base_dir', '/home/pi/prusa-camera/captures'))
        base_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.get('storage', {}).get('organize_by_date', True):
            date_dir = base_dir / datetime.now().strftime('%Y-%m-%d')
            date_dir.mkdir(exist_ok=True)
            session_name = datetime.now().strftime('%H%M%S')
            self.current_session_dir = date_dir / session_name
        else:
            session_name = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.current_session_dir = base_dir / session_name
        
        self.current_session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save session metadata
        metadata = {
            'start_time': datetime.now().isoformat(),
            'config_snapshot': self.config
        }
        with open(self.current_session_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Print session directory: {self.current_session_dir}")
    
    def _end_print_session(self) -> None:
        """End the current print session."""
        if not self.print_active:
            return
        
        self.logger.info(f"Print session ended. Captured {self.capture_counter} images")
        
        # Update metadata
        if self.current_session_dir:
            metadata_file = self.current_session_dir / 'metadata.json'
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                metadata['end_time'] = datetime.now().isoformat()
                metadata['total_images'] = self.capture_counter
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                self.logger.warning(f"Failed to update metadata: {e}")
        
        self.print_active = False
    
    def _capture_image(self, trigger_type: str = "manual") -> Optional[Path]:
        """Capture an image from the camera."""
        try:
            if not self.current_session_dir:
                self._start_print_session()
            
            # Increment counter
            self.capture_counter += 1
            
            # Generate filename
            pattern = self.config.get('storage', {}).get('filename_pattern', 'img_{counter:05d}.jpg')
            filename = pattern.format(
                counter=self.capture_counter,
                timestamp=int(time.time()),
                date=datetime.now().strftime('%Y%m%d'),
                time=datetime.now().strftime('%H%M%S')
            )
            
            output_path = self.current_session_dir / filename
            
            # Build libcamera-still command
            cmd = ['libcamera-still', '-o', str(output_path), '-n', '-t', '1']
            
            # Add camera settings
            cam_config = self.config.get('camera', {})
            
            # Resolution
            resolution = cam_config.get('resolution', 'max')
            if resolution != 'max' and 'x' in str(resolution):
                width, height = resolution.split('x')
                cmd.extend(['--width', width, '--height', height])
            
            # Quality
            quality = cam_config.get('quality', 85)
            cmd.extend(['--quality', str(quality)])
            
            # Rotation
            rotation = cam_config.get('rotation', 0)
            if rotation:
                cmd.extend(['--rotation', str(rotation)])
            
            # Flip
            if cam_config.get('hflip', False):
                cmd.append('--hflip')
            if cam_config.get('vflip', False):
                cmd.append('--vflip')
            
            # ISO
            iso = cam_config.get('iso', 'auto')
            if iso != 'auto':
                cmd.extend(['--analoggain', str(float(iso) / 100)])
            
            # Shutter speed
            shutter = cam_config.get('shutter_speed', 'auto')
            if shutter != 'auto':
                cmd.extend(['--shutter', str(shutter)])
            
            # AWB mode
            awb = cam_config.get('awb_mode', 'auto')
            cmd.extend(['--awb', awb])
            
            # Capture image
            self.logger.debug(f"Capturing image: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=self.config.get('advanced', {}).get('capture_timeout', 10)
            )
            
            self.logger.info(f"Image captured: {filename} (trigger: {trigger_type})")
            
            # Upload to Prusa Connect if enabled
            if self.config.get('prusa_connect', {}).get('enabled', True):
                self._upload_to_prusa_connect(output_path)
            
            return output_path
            
        except subprocess.TimeoutExpired:
            self.logger.error("Camera capture timeout")
            return None
        except Exception as e:
            self.logger.error(f"Failed to capture image: {e}")
            return None
    
    def _upload_to_prusa_connect(self, image_path: Path) -> bool:
        """Upload image to Prusa Connect."""
        try:
            # Check upload interval
            current_time = time.time()
            min_interval = self.config.get('prusa_connect', {}).get('upload_interval', 10)
            if current_time - self.last_upload_time < min_interval:
                self.logger.debug("Skipping upload (interval not reached)")
                return False
            
            token = self.config.get('prusa_connect', {}).get('token', '')
            if not token or token == 'YOUR_PRUSA_CONNECT_TOKEN_HERE':
                self.logger.debug("Prusa Connect token not configured, skipping upload")
                return False
            
            fingerprint = self.config.get('prusa_connect', {}).get('printer_fingerprint', '')
            
            # Prusa Connect camera upload endpoint
            url = f"https://connect.prusa3d.com/c/snapshot"
            
            headers = {
                'Token': token,
                'Fingerprint': fingerprint
            }
            
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.put(url, headers=headers, files=files, timeout=10)
            
            if response.status_code == 200:
                self.logger.debug("Image uploaded to Prusa Connect")
                self.last_upload_time = current_time
                return True
            else:
                self.logger.warning(f"Prusa Connect upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Failed to upload to Prusa Connect: {e}")
            return False
    
    def _time_based_capture_loop(self) -> None:
        """Time-based capture loop (runs in separate thread)."""
        self.logger.info("Time-based capture thread started")
        
        while self.running:
            try:
                time_config = self.config.get('capture', {}).get('time_mode', {})
                
                if not time_config.get('enabled', True):
                    time.sleep(1)
                    continue
                
                interval = time_config.get('interval', 30)
                only_during_print = time_config.get('only_during_print', True)
                
                # Check if we should capture
                should_capture = True
                if only_during_print and not self.print_active:
                    should_capture = False
                
                if should_capture:
                    self._capture_image("time")
                
                # Sleep for interval
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in time-based capture loop: {e}")
                time.sleep(5)
        
        self.logger.info("Time-based capture thread stopped")
    
    def start(self) -> None:
        """Start the camera service."""
        self.logger.info("Starting camera service...")
        self.running = True
        
        # Start time-based capture thread if enabled
        if self.config.get('capture', {}).get('time_mode', {}).get('enabled', True):
            self.time_capture_thread = threading.Thread(
                target=self._time_based_capture_loop,
                daemon=True
            )
            self.time_capture_thread.start()
        
        self.logger.info("Camera service started")
        self.logger.info("Waiting for triggers...")
        
        # Main loop
        try:
            while self.running:
                time.sleep(1)
                
                # Check system resources
                if psutil.virtual_memory().percent > 90:
                    self.logger.warning("High memory usage detected")
                if psutil.disk_usage('/').percent > 90:
                    self.logger.warning("Low disk space detected")
                    
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the camera service."""
        self.logger.info("Stopping camera service...")
        self.running = False
        
        # End active print session
        if self.print_active:
            self._end_print_session()
        
        # Wait for time capture thread
        if self.time_capture_thread and self.time_capture_thread.is_alive():
            self.time_capture_thread.join(timeout=5)
        
        # Cleanup GPIO
        if self.trigger_button:
            self.trigger_button.close()
        
        self.logger.info("Camera service stopped")
    
    def trigger_compile_video(self) -> None:
        """Trigger video compilation (called by external script)."""
        self.logger.info("Video compilation triggered")
        
        # End print session
        self._end_print_session()
        
        if not self.current_session_dir:
            self.logger.warning("No active session directory for video compilation")
            return
        
        # Call compilation script
        try:
            script_path = Path(__file__).parent / "compile_video.sh"
            subprocess.Popen(
                [str(script_path), str(self.current_session_dir)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.logger.info("Video compilation script launched")
        except Exception as e:
            self.logger.error(f"Failed to launch compilation script: {e}")


def main():
    """Main entry point."""
    # Setup signal handlers
    service = None
    
    def signal_handler(signum, frame):
        if service:
            service.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check for special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == 'compile':
            # Trigger compilation for current session
            config_path = sys.argv[2] if len(sys.argv) > 2 else "/home/pi/prusa-camera/config.yaml"
            service = CameraService(config_path)
            service.trigger_compile_video()
            return
    
    # Start service
    config_path = sys.argv[1] if len(sys.argv) > 1 else "/home/pi/prusa-camera/config.yaml"
    service = CameraService(config_path)
    service.start()


if __name__ == '__main__':
    main()

