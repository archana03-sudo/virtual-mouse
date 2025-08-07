import cv2
import mediapipe as mp
import pyautogui
import time
import threading
import tkinter as tk
from tkinter import ttk

# 👇 First, create a root window (required for BooleanVar)
root = tk.Tk()
root.withdraw()  # We hide it for now, will create new one for GUI

# 📷 Mediapipe and Webcam Init
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
hand_detector = mp.solutions.hands.Hands(max_num_hands=1)
drawing_utils = mp.solutions.drawing_utils
screen_width, screen_height = pyautogui.size()

# 🟢 Global toggle flags
gesture_flags = {
    "Move": tk.BooleanVar(value=True),
    "Click": tk.BooleanVar(value=True),
    "Scroll": tk.BooleanVar(value=True),
    "Drag": tk.BooleanVar(value=True),
    "Running": tk.BooleanVar(value=False)
}

# ✋ Smoothening
plocX, plocY = 0, 0
clocX, clocY = 0, 0
smoothening = 5
drag = False

# 🖱️ Main Virtual Mouse Logic
def virtual_mouse():
    global plocX, plocY, clocX, clocY, drag

    while True:
        if not gesture_flags["Running"].get():
            time.sleep(0.1)
            continue

        _, frame = cap.read()
        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = hand_detector.process(rgb_frame)
        hands = output.multi_hand_landmarks

        if hands:
            for hand in hands:
                drawing_utils.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
                landmarks = hand.landmark

                index_finger = landmarks[8]
                middle_finger = landmarks[12]
                ring_finger = landmarks[16]
                thumb = landmarks[4]

                x = int(index_finger.x * frame_width)
                y = int(index_finger.y * frame_height)
                screen_x = screen_width / frame_width * x
                screen_y = screen_height / frame_height * y

                # 👉 MOVE
                if gesture_flags["Move"].get():
                    clocX = plocX + (screen_x - plocX) / smoothening
                    clocY = plocY + (screen_y - plocY) / smoothening
                    pyautogui.moveTo(clocX, clocY)
                    plocX, plocY = clocX, clocY
                    cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)

                # 👆 CLICK
                if gesture_flags["Click"].get():
                    index_middle_dist = abs((index_finger.y - middle_finger.y) * frame_height)
                    if index_middle_dist < 40:
                        pyautogui.click()
                        time.sleep(0.3)

                # 🖱️ SCROLL
                if gesture_flags["Scroll"].get():
                    index_middle_dist = abs((index_finger.y - middle_finger.y) * frame_height)
                    index_ring_dist = abs((index_finger.y - ring_finger.y) * frame_height)

                    if middle_finger.y < index_finger.y and index_middle_dist > 50:
                        pyautogui.scroll(50)
                        time.sleep(0.2)
                    elif ring_finger.y < index_finger.y and index_ring_dist > 50:
                        pyautogui.scroll(-50)
                        time.sleep(0.2)

                # ✊ DRAG
                if gesture_flags["Drag"].get():
                    index_thumb_dist = abs((index_finger.x - thumb.x) * frame_width)
                    if index_thumb_dist < 20:
                        if not drag:
                            drag = True
                            pyautogui.mouseDown()
                    else:
                        if drag:
                            drag = False
                            pyautogui.mouseUp()

        cv2.imshow("Virtual Mouse", frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# 🖥️ GUI Toggle Window
def start_gui():
    gui = tk.Tk()
    gui.title("🖱️ Virtual Mouse Controller")
    gui.geometry("250x300")
    gui.resizable(False, False)

    tk.Label(gui, text="Gesture Control Panel", font=("Arial", 14, "bold")).pack(pady=10)

    for gesture, var in gesture_flags.items():
        if gesture != "Running":
            cb = tk.Checkbutton(gui, text=gesture, variable=var, font=("Arial", 11))
            cb.pack(anchor='w', padx=20)

    def toggle_run():
        gesture_flags["Running"].set(not gesture_flags["Running"].get())
        run_btn.config(text="🟢 Stop" if gesture_flags["Running"].get() else "▶️ Start")

    run_btn = ttk.Button(gui, text="▶️ Start", command=toggle_run)
    run_btn.pack(pady=15)

    gui.mainloop()

# 🧵 Parallel execution
threading.Thread(target=virtual_mouse, daemon=True).start()
start_gui()
