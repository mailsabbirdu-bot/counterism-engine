# ==============================================================================
# COUNTERISM STUDIO V4 — QUICK OVERLAY TEST (COLAB)
# ==============================================================================
# This script should be run in a Google Colab Cell.

import os
import shutil

# 1. Setup Environment
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"

if not os.path.exists(PROJECT_NAME):
    print("❌ Project not found. Please run the full colab.md setup first.")
else:
    os.chdir(PROJECT_NAME)

    # 2. Sync Drive Assets to Public Folder
    # This ensures that 'renders' and 'audio' are available to Remotion
    print("🔗 Syncing Drive assets to public folder...")
    os.makedirs("public/renders", exist_ok=True)
    drive_renders = f"{DRIVE_BASE_PATH}/renders"
    if os.path.exists(drive_renders):
        # Using recursive copy for symlinks if possible, or just copy
        os.system(f"cp -rs {drive_renders}/* public/renders/ 2>/dev/null || true")

    # 3. Run the specialized test render
    print("\n🎬 STARTING QUICK OVERLAY TEST...")
    print("--------------------------------------------------------------------------------")
    # This renders only the colab_test.json and outputs to overlay_test.mp4
    os.system("npm run render -- --template=colab_test.json --output=overlay_test.mp4")

    # 4. Save to Google Drive
    LOCAL_RENDER_DIR = "renders/overlays/remotion/overlay_test.mp4"
    DRIVE_RENDER_DIR = f"{DRIVE_BASE_PATH}/renders/overlays/remotion/overlay_test.mp4"

    if os.path.exists(LOCAL_RENDER_DIR):
        print(f"📤 Uploading overlay_test.mp4 to Drive...")
        os.makedirs(os.path.dirname(DRIVE_RENDER_DIR), exist_ok=True)
        shutil.copy(LOCAL_RENDER_DIR, DRIVE_RENDER_DIR)
        print(f"\n✅ Test render saved to: {DRIVE_RENDER_DIR}")
    else:
        print("❌ Test render failed or file not found.")
