# 🔄 Counterism Studio V4 - Scene Replacement Utility

Use this cell to replace original rendered scenes with updated versions from the `remake/` folder.

```python
import os
import shutil
import glob

# Paths
DRIVE_BASE = "/content/drive/MyDrive/Counterism_Studio_V4/renders/overlays/remotion"
REMAKE_DIR = os.path.join(DRIVE_BASE, "remake")

if not os.path.exists(REMAKE_DIR):
    print(f"⚠️ Remake directory not found: {REMAKE_DIR}")
else:
    remake_files = glob.glob(os.path.join(REMAKE_DIR, "updated_scene_SCENE_*.mp4"))

    if not remake_files:
        print("ℹ️ No remake files found to replace.")
    else:
        print(f"🔄 Found {len(remake_files)} remake files. Starting replacement...")

        for src in remake_files:
            filename = os.path.basename(src)
            # updated_scene_SCENE_01.mp4 -> updated_scene_SC_01.mp4
            # Or the original naming convention used in the main output?
            # User manifest uses: video_path: renders/scene_SC_01.mp4
            # But the scene rendering loop in render.ts outputs updated_scene_SCENE_01.mp4 to DRIVE_BASE.

            dst = os.path.join(DRIVE_BASE, filename)

            print(f"   🚀 Replacing {filename}...")
            shutil.copy2(src, dst)

        print("\n✅ All scenes successfully replaced and synchronized.")
```
