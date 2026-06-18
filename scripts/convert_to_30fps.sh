#!/bin/bash

TARGET_DIR=$1

if [ -z "$TARGET_DIR" ]; then
    echo "Usage: $0 <target_directory>"
    exit 1
fi

# Function to find ffmpeg
get_ffmpeg() {
    if command -v ffmpeg >/dev/null 2>&1; then
        echo "ffmpeg"
    else
        echo "npx remotion ffmpeg"
    fi
}

FFMPEG=$(get_ffmpeg)
echo "Using FFMPEG: $FFMPEG"

# Iterate over all mp4 files in the target directory
for file in "$TARGET_DIR"/*.mp4; do
    if [ -f "$file" ]; then
        echo "Processing: $file"
        temp_file="${file%.mp4}_30fps.mp4"

        # Convert to 30fps
        # Using -r 30 for better compatibility with Remotion's ffmpeg build
        $FFMPEG -i "$file" -r 30 -y "$temp_file" -hide_banner -loglevel error

        if [ $? -eq 0 ]; then
            mv "$temp_file" "$file"
            echo "Successfully converted $file to 30fps"
        else
            echo "Failed to convert $file"
            rm -f "$temp_file"
        fi
    fi
done
