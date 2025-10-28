#!/bin/bash
#
# Prusa Timelapse Video Compilation Script
#
# Compiles captured images into a timelapse video using ffmpeg,
# uploads to NAS, and cleans up source files.
#
# Usage: ./compile_video.sh [session_directory]
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.yaml"
LOG_FILE="${SCRIPT_DIR}/logs/compile_video.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    for cmd in ffmpeg python3 yq; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Install with: sudo apt install ffmpeg python3 yq"
        exit 1
    fi
}

# Parse YAML config using Python
parse_config() {
    python3 - <<EOF
import yaml
import sys

try:
    with open('${CONFIG_FILE}', 'r') as f:
        config = yaml.safe_load(f)
    
    # Export video settings as environment variables
    video = config.get('video', {})
    print(f"export VIDEO_FRAMERATE={video.get('framerate', 30)}")
    print(f"export VIDEO_CODEC={video.get('codec', 'libx264')}")
    print(f"export VIDEO_PRESET={video.get('preset', 'medium')}")
    print(f"export VIDEO_CRF={video.get('crf', 23)}")
    print(f"export VIDEO_RESOLUTION='{video.get('output_resolution', '1920x1080')}'")
    print(f"export VIDEO_FILENAME_PATTERN='{video.get('filename_pattern', 'timelapse_{date}_{time}.mp4')}'")
    
    # Export storage settings
    storage = config.get('storage', {})
    print(f"export KEEP_IMAGES={'true' if storage.get('keep_images_after_compile', False) else 'false'}")
    
    # Export NAS settings
    nas = config.get('nas', {})
    print(f"export NAS_ENABLED={'true' if nas.get('enabled', False) else 'false'}")
    print(f"export NAS_PROTOCOL={nas.get('protocol', 'smb')}")
    print(f"export DELETE_AFTER_UPLOAD={'true' if nas.get('delete_after_upload', True) else 'false'}")
    print(f"export RETRY_ATTEMPTS={nas.get('retry_attempts', 3)}")
    
    if nas.get('protocol') == 'smb':
        smb = nas.get('smb', {})
        print(f"export SMB_SERVER={smb.get('server', '')}")
        print(f"export SMB_SHARE={smb.get('share', '')}")
        print(f"export SMB_PATH={smb.get('path', '')}")
        print(f"export SMB_USERNAME={smb.get('username', '')}")
        print(f"export SMB_PASSWORD={smb.get('password', '')}")
        print(f"export SMB_DOMAIN={smb.get('domain', 'WORKGROUP')}")
    else:
        nfs = nas.get('nfs', {})
        print(f"export NFS_SERVER={nfs.get('server', '')}")
        print(f"export NFS_EXPORT={nfs.get('export', '')}")
        print(f"export NFS_PATH={nfs.get('path', '')}")
    
except Exception as e:
    print(f"Error parsing config: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# Get session directory
if [ -n "$1" ]; then
    SESSION_DIR="$1"
else
    # Find most recent session
    BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_FILE}'))['storage']['base_dir'])")
    SESSION_DIR=$(find "$BASE_DIR" -type d -name "[0-9]*" | sort -r | head -n 1)
fi

if [ -z "$SESSION_DIR" ] || [ ! -d "$SESSION_DIR" ]; then
    log_error "Session directory not found: $SESSION_DIR"
    exit 1
fi

log "Starting video compilation for session: $SESSION_DIR"

# Check for images
IMAGE_COUNT=$(find "$SESSION_DIR" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    log_error "No images found in $SESSION_DIR"
    exit 1
fi

log "Found $IMAGE_COUNT images to compile"

# Parse configuration
check_dependencies
eval "$(parse_config)"

# Generate output filename
DATE=$(date '+%Y%m%d')
TIME=$(date '+%H%M%S')
OUTPUT_FILENAME="${VIDEO_FILENAME_PATTERN//\{date\}/$DATE}"
OUTPUT_FILENAME="${OUTPUT_FILENAME//\{time\}/$TIME}"
OUTPUT_PATH="${SESSION_DIR}/${OUTPUT_FILENAME}"

log "Output video: $OUTPUT_PATH"

# Create temporary file list for ffmpeg
FILELIST="${SESSION_DIR}/filelist.txt"
find "$SESSION_DIR" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | sort | while read -r img; do
    echo "file '$(basename "$img")'" >> "$FILELIST"
done

# Build ffmpeg command
FFMPEG_CMD="ffmpeg -y -f concat -safe 0 -i ${FILELIST}"
FFMPEG_CMD="$FFMPEG_CMD -framerate ${VIDEO_FRAMERATE}"
FFMPEG_CMD="$FFMPEG_CMD -c:v ${VIDEO_CODEC}"
FFMPEG_CMD="$FFMPEG_CMD -preset ${VIDEO_PRESET}"
FFMPEG_CMD="$FFMPEG_CMD -crf ${VIDEO_CRF}"

# Add resolution scaling if not source
if [ "$VIDEO_RESOLUTION" != "source" ]; then
    FFMPEG_CMD="$FFMPEG_CMD -vf scale=${VIDEO_RESOLUTION}:force_original_aspect_ratio=decrease,pad=${VIDEO_RESOLUTION}:(ow-iw)/2:(oh-ih)/2"
fi

FFMPEG_CMD="$FFMPEG_CMD -pix_fmt yuv420p"
FFMPEG_CMD="$FFMPEG_CMD ${OUTPUT_PATH}"

# Compile video
log "Compiling video with ffmpeg..."
log "Command: $FFMPEG_CMD"

cd "$SESSION_DIR"
if eval "$FFMPEG_CMD" 2>&1 | tee -a "$LOG_FILE"; then
    log "Video compiled successfully"
    
    # Get video size
    VIDEO_SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
    log "Video size: $VIDEO_SIZE"
    
    # Clean up filelist
    rm -f "$FILELIST"
else
    log_error "Video compilation failed"
    rm -f "$FILELIST"
    exit 1
fi

# Upload to NAS if enabled
if [ "$NAS_ENABLED" = "true" ]; then
    log "Uploading video to NAS..."
    
    UPLOAD_SUCCESS=false
    
    for attempt in $(seq 1 "$RETRY_ATTEMPTS"); do
        log "Upload attempt $attempt of $RETRY_ATTEMPTS"
        
        if [ "$NAS_PROTOCOL" = "smb" ]; then
            # SMB upload using smbclient
            SMB_URL="//${SMB_SERVER}/${SMB_SHARE}"
            REMOTE_PATH="${SMB_PATH}/$(basename "$OUTPUT_PATH")"
            
            if smbclient "$SMB_URL" -U "${SMB_USERNAME}%${SMB_PASSWORD}" -W "$SMB_DOMAIN" -c "cd ${SMB_PATH}; put ${OUTPUT_PATH} $(basename "$OUTPUT_PATH")" 2>&1 | tee -a "$LOG_FILE"; then
                log "Video uploaded successfully to SMB share"
                UPLOAD_SUCCESS=true
                break
            else
                log_error "SMB upload attempt $attempt failed"
            fi
        else
            # NFS upload (mount, copy, unmount)
            MOUNT_POINT="/tmp/nfs_mount_$$"
            mkdir -p "$MOUNT_POINT"
            
            if mount -t nfs "${NFS_SERVER}:${NFS_EXPORT}" "$MOUNT_POINT" 2>&1 | tee -a "$LOG_FILE"; then
                DEST_DIR="${MOUNT_POINT}/${NFS_PATH}"
                mkdir -p "$DEST_DIR"
                
                if cp "$OUTPUT_PATH" "${DEST_DIR}/$(basename "$OUTPUT_PATH")" 2>&1 | tee -a "$LOG_FILE"; then
                    log "Video uploaded successfully to NFS share"
                    UPLOAD_SUCCESS=true
                fi
                
                umount "$MOUNT_POINT"
                rmdir "$MOUNT_POINT"
                
                if [ "$UPLOAD_SUCCESS" = true ]; then
                    break
                fi
            else
                log_error "NFS mount attempt $attempt failed"
                rmdir "$MOUNT_POINT" 2>/dev/null || true
            fi
        fi
        
        if [ "$attempt" -lt "$RETRY_ATTEMPTS" ]; then
            sleep 5
        fi
    done
    
    if [ "$UPLOAD_SUCCESS" = true ]; then
        log "NAS upload completed successfully"
        
        # Delete local video if configured
        if [ "$DELETE_AFTER_UPLOAD" = "true" ]; then
            log "Deleting local video after successful upload"
            rm -f "$OUTPUT_PATH"
        fi
    else
        log_error "All NAS upload attempts failed"
    fi
fi

# Clean up images if configured
if [ "$KEEP_IMAGES" = "false" ]; then
    log "Cleaning up source images..."
    find "$SESSION_DIR" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | xargs rm -f
    log "Source images deleted"
fi

log "Video compilation complete!"

# Print summary
log "=== Compilation Summary ==="
log "Session: $SESSION_DIR"
log "Images processed: $IMAGE_COUNT"
log "Output video: $OUTPUT_PATH"
log "Video size: $VIDEO_SIZE"
log "NAS upload: $([ "$NAS_ENABLED" = "true" ] && echo "Enabled" || echo "Disabled")"
log "=========================="

exit 0

