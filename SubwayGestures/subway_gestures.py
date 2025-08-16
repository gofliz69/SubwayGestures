# subway_gestures.py
# "Earlier" neutral-circle model with friendlier tuning + optional auto-rearm.
# Index fingertip tracking, simple swipe detection, preview ON by default.

import os, time
from collections import deque
import cv2
import mediapipe as mp
import pyautogui

# ------------- Settings (tweak here) -------------
SEND_KEYS        = True       # True: control game; False: print ACTION only
HEADLESS_LIVE    = False      # False = show preview window (recommended)
USE_WASD         = False      # Set True to send WASD instead of arrows

# Camera
CAM_INDEX        = 0
FRAME_WIDTH      = 640
FRAME_HEIGHT     = 480

# Motion window & sensitivity
HISTORY_SEC      = 0.45       # how long we look back for motion
COOLDOWN_SEC     = 0.45       # min time between actions
DX_THRESH        = 0.18       # horizontal distance (0..1)
DY_THRESH        = 0.15       # vertical distance (0..1)

# Neutral zone gating (one swipe -> one action)
NEUTRAL_RADIUS   = 0.22       # BIGGER circle = easier re-arm
NEUTRAL_HOLD     = 0.08       # hover this long near center to re-arm
AUTO_REARM_SEC   = 0.55       # also re-arm after this time (even if not centered)

# Hand tracking confidence
MIN_CONFIDENCE   = 0.6
# -------------------------------------------------

# Less picky about mouse-at-corner
pyautogui.FAILSAFE = False
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

# Camera (prefer AVFoundation on macOS)
cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_AVFOUNDATION)
if not cap.isOpened():
    cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam. Try a different CAM_INDEX or check permissions.")

if FRAME_WIDTH and FRAME_HEIGHT:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# State
history = deque()            # (t, x, y) fingertip coords in [0..1]
last_action_time = 0.0
neutral_since = 0.0
can_trigger = True

def in_neutral(x, y, cx=0.5, cy=0.5):
    dx, dy = x - cx, y - cy
    return (dx*dx + dy*dy) ** 0.5 <= NEUTRAL_RADIUS

def tap(direction: str):
    if not SEND_KEYS:
        print(f"ACTION: {direction.upper()}")
        return
    if USE_WASD:
        mapping = {"left":"a","right":"d","up":"w","down":"s"}
        pyautogui.press(mapping[direction])
    else:
        pyautogui.press(direction)

def detect_swipe():
    """Return 'left'|'right'|'up'|'down' or None based on net motion."""
    if len(history) < 2:
        return None
    t0, x0, y0 = history[0]
    t1, x1, y1 = history[-1]
    dx, dy = x1 - x0, y1 - y0

    # dominant axis
    if abs(dx) >= abs(dy):
        if dx <= -DX_THRESH: return "left"
        if dx >=  DX_THRESH: return "right"
    else:
        if dy <= -DY_THRESH: return "up"     # up = y decreases
        if dy >=  DY_THRESH: return "down"
    return None

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=MIN_CONFIDENCE,
    min_tracking_confidence=0.5
) as hands:

    print(f"Mode: {'LIVE (keys sent)' if SEND_KEYS else 'TEST (no keys)'} | "
          f"Preview: {not HEADLESS_LIVE} | Tip: click the game canvas to focus")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)
        now = time.time()

        # --- Auto re-arm after a short time, even if not perfectly centered
        if not can_trigger and now - last_action_time >= AUTO_REARM_SEC:
            can_trigger = True

        # Keep only recent points
        while history and now - history[0][0] > HISTORY_SEC:
            history.popleft()

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark[8]  # index fingertip
            cx, cy = lm.x, lm.y
            history.append((now, cx, cy))

            # Neutral gating based on fixed center (screen center)
            if in_neutral(cx, cy, 0.5, 0.5):
                if neutral_since == 0.0:
                    neutral_since = now
                elif now - neutral_since >= NEUTRAL_HOLD:
                    can_trigger = True
            else:
                neutral_since = 0.0

            # Decide swipe if armed + cooldown passed
            if can_trigger and (now - last_action_time >= COOLDOWN_SEC):
                action = detect_swipe()
                if action:
                    last_action_time = now
                    can_trigger = False
                    tap(action)
                    if not (SEND_KEYS and HEADLESS_LIVE):
                        cv2.putText(frame, f"ACTION: {action.upper()}",
                                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)

            # Draw preview HUD
            if not (SEND_KEYS and HEADLESS_LIVE):
                mp_draw.draw_landmarks(frame, res.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)
                # Big neutral circle centered on screen center
                rad_px = int(NEUTRAL_RADIUS * min(w, h))
                cv2.circle(frame, (w//2, h//2), rad_px, (220, 220, 220), 2)
                # Fingertip marker
                cv2.circle(frame, (int(cx*w), int(cy*h)), 10, (255,255,255), 2)
                cv2.putText(frame, "LIVE" if SEND_KEYS else "TEST",
                            (10, h-15), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0,255,0) if SEND_KEYS else (200,200,200), 2)
        else:
            # No hand: just let history decay; keep gating state
            pass

        # Window handling
        if not (SEND_KEYS and HEADLESS_LIVE):
            cv2.imshow("Subway Surfers - Gestures (Classic Neutral)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                break
        else:
            # headless loop pacing
            time.sleep(0.005)

cap.release()
cv2.destroyAllWindows()
