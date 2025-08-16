
# Subway Surfers – Hand Gesture Controller (Python + MediaPipe)

Control **Subway Surfers** in the browser using quick hand swipes captured by your webcam.  
No hardware gloves, no ML training—just **MediaPipe**, **OpenCV**, and **pyautogui**.

https://github.com/<your-username>/SubwayGestures


---

## ✨ Features
- **Swipe to play:** Left/Right/Up/Down hand flicks → arrow keys (or WASD).
- **Neutral circle gating:** One swipe = one action (prevents double-triggers).
- **Preview window:** See landmarks + neutral circle for easy tuning.
- **Browser-friendly:** Optimized for **Poki/Chrome** with reliable key delivery via `pyautogui`.
- **macOS ready:** Works with Continuity Camera or built-in webcam.

---

## 🧰 Tech
- Python 3.9+
- [MediaPipe Hands](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)
- OpenCV
- pyautogui (sends keys to the frontmost app)
- (Optional) pynput

---

## 🚀 Quick Start

```bash
# 1) Clone
git clone https://github.com/<your-username>/SubwayGestures.git
cd SubwayGestures

# 2) Create & activate a venv
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows PowerShell

# 3) Install deps
pip install -r requirements.txt

# 4) Run
python3 subway_gestures.py
