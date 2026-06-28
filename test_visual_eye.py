import os
import json
from visual_eye.analyzer import analyze_video
import numpy as np
import cv2

# Create a dummy video for testing
def create_dummy_video(path):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, 30.0, (1920, 1080))
    for _ in range(30):
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        cv2.putText(frame, "Dummy Video", (800, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        out.write(frame)
    out.release()

test_video = "test_video.mp4"
output_dir = "public/renders/analysis"

if not os.path.exists("public/renders"):
    os.makedirs("public/renders")

create_dummy_video(test_video)

print("Running Visual Eye Analysis...")
analysis = analyze_video(test_video, output_dir)

print(f"Status: {analysis.status}")
print(f"Scene Type: {analysis.scene_type}")
print(f"Safe Regions: {len(analysis.safe_text_regions)}")

analysis_file = os.path.join(output_dir, "test_video_analysis.json")
if os.path.exists(analysis_file):
    print(f"✅ Success: Analysis saved to {analysis_file}")
else:
    print("❌ Error: Analysis file not found")

# Cleanup
if os.path.exists(test_video):
    os.remove(test_video)
