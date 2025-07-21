import json
from pynput import keyboard
import pygetwindow as gw
import win32gui, win32con

recorded_keys = []
def move_and_resize_window(title, x, y, width, height):
    window = gw.getWindowsWithTitle(title)
    if window:
        hwnd = window[0]._hWnd
        win32gui.SetWindowPos(hwnd, None, x, y, width, height, win32con.SWP_NOZORDER)
        
ARROW_KEYS = {
    keyboard.Key.left: 'left',
    keyboard.Key.right: 'right',
    keyboard.Key.up: 'up',
    keyboard.Key.down: 'down'
}

def on_press(key):
    if key == keyboard.Key.esc:
        print("🛑 Recording stopped.")
        return False

    if key in ARROW_KEYS:
        key_str = ARROW_KEYS[key]
        # timestamp는 0으로 고정해서 저장 (호환 위해)
        recorded_keys.append([key_str])
        print(f"▶ {key_str} pressed")

def save_to_json(filename="mapData.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(recorded_keys, f, ensure_ascii=False, indent=2)
    print(f"✅ 방향키 기록 저장 완료: {filename}")

def record_keys():
    move_and_resize_window("MapleStory Worlds-바람의나라 클래식", 0, 0, 1280,750)
    print("⏺️ 방향키 기록 시작 (ESC 키로 종료)")
    from pynput import keyboard as pkb
    with pkb.Listener(on_press=on_press) as listener:
        listener.join()
    save_to_json()

if __name__ == "__main__":
    record_keys()
