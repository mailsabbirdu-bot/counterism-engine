# ☁️ Google Colab Setup (Counterism Studio V4)

Run the following cell in Google Colab to automate the entire process:

```python
# Install dependencies, clone repository, and run the rendering pipeline
!apt-get update && apt-get install -y ffmpeg build-essential
!git clone https://github.com/mailsabbirdu-bot/counterism-engine
%cd counterism-engine
!npm install
!npm run render
```
