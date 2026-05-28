# 🧪 Counterism Studio V4 — Quick Overlay Test

Run the following cell in Google Colab to verify video and image overlays in a lightweight environment.

```python
# ==============================================================================
# COUNTERISM STUDIO V4 — QUICK OVERLAY VERIFICATION
# ==============================================================================
import os
import shutil

# 1. Mount Google Drive
from google.colab import drive
print("📂 Mounting Google Drive...")
drive.mount('/content/drive')

# 2. Setup Project Environment
PROJECT_NAME = "counterism-engine"
DRIVE_BASE_PATH = "/content/drive/MyDrive/Counterism_Studio_V4"
REPO_URL = "https://github.com/mailsabbirdu-bot/counterism-engine"

if not os.path.exists(PROJECT_NAME):
    print(f"🚀 Cloning repository: {REPO_URL}")
    !git clone {REPO_URL}
else:
    print(f"✅ Project folder '{PROJECT_NAME}' already exists.")

%cd {PROJECT_NAME}

# 3. Link Drive Assets
print("🔗 Linking Drive assets to project...")
# Create a robust symbolic link to the renders directory
!rm -rf public/renders
!ln -s "{DRIVE_BASE_PATH}/renders" public/renders
print(f"✅ Assets linked from {DRIVE_BASE_PATH}/renders:")
!ls public/renders/

# 4. Install Dependencies
print("📦 Installing dependencies...")
!apt-get update -y && apt-get install -y ffmpeg build-essential
!npm install

# 5. Run Specialized Test Render
print("\n🎬 STARTING QUICK OVERLAY TEST...")
print("--------------------------------------------------------------------------------")
# This command uses the specialized Colab_Test.json and outputs to overlay_test.mp4
# Concurrency is set to 1 for maximum stability
!npm run render -- --template=Colab_Test.json --output=overlay_test.mp4 --concurrency=1

# 6. Save Result to Drive
LOCAL_TEST_FILE = "renders/overlays/remotion/overlay_test.mp4"
DRIVE_TEST_DEST = f"{DRIVE_BASE_PATH}/renders/overlays/remotion/overlay_test.mp4"

if os.path.exists(LOCAL_TEST_FILE):
    print(f"📤 Uploading result to Drive: {DRIVE_TEST_DEST}")
    os.makedirs(os.path.dirname(DRIVE_TEST_DEST), exist_ok=True)
    shutil.copy(LOCAL_TEST_FILE, DRIVE_TEST_DEST)
    print("\n✅ QUICK TEST COMPLETE. Check your Drive for 'overlay_test.mp4'!")
else:
    print("❌ Test render failed.")
```
