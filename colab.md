# ☁️ Google Colab Setup (Counterism Studio V4)

Run these cells in a Google Colab environment:

## 1. Install System Dependencies
```bash
!apt-get update && apt-get install -y ffmpeg build-essential
```

## 2. Clone and Setup
```bash
!git clone <your-repo-url>
%cd counterism-studio-v4
!npm install
```

## 3. Render
```bash
!npm run render
```
