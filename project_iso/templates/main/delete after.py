import pyautogui
import time

# --- Configuration ---
CLICKS_PER_SECOND = 5
DELAY = 1 / CLICKS_PER_SECOND
# ---------------------

print("Script starting in 5 seconds...")
print("Move your mouse to the target area!")
time.sleep(5)

try:
    print("Clicking started. Move mouse to any corner of the screen to stop.")
    while True:
        pyautogui.click()
        time.sleep(DELAY)
except pyautogui.FailSafeException:
    print("\nFail-safe triggered. Script stopped.")