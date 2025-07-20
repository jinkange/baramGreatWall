import time
import os
import cv2
import numpy as np
from PIL import ImageGrab
import keyboard
import threading
import requests
import win32console
import win32gui
import win32con
import datetime
import sys
import win32gui
import win32con
import pyautogui
import threading
import keyboard
import time
import win32process
import win32api

EXPIRE_DATE = datetime.datetime(2025, 9, 1)
target_title = "MapleStory Worlds-바람의나라 클래식"
running = False
def find_window(title):
    hwnd = None

    def enum_handler(h, _):
        nonlocal hwnd
        if win32gui.IsWindowVisible(h):
            window_title = win32gui.GetWindowText(h)
            if title.lower() in window_title.lower():
                hwnd = h

    win32gui.EnumWindows(enum_handler, None)
    return hwnd


def activate_window(hwnd):
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        # 현재 쓰레드 ID와 대상 윈도우 쓰레드 ID 연결
        fg_window = win32gui.GetForegroundWindow()
        current_thread = win32api.GetCurrentThreadId()
        target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
        fg_thread, _ = win32process.GetWindowThreadProcessId(fg_window)

        win32process.AttachThreadInput(current_thread, target_thread, True)
        win32process.AttachThreadInput(current_thread, fg_thread, True)

        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"⚠️ SetForegroundWindow 실패: {e}")

        # 다시 연결 해제
        win32process.AttachThreadInput(current_thread, target_thread, False)
        win32process.AttachThreadInput(current_thread, fg_thread, False)

        time.sleep(0.2)
def move_loop():
    global running
    while True:
        if running:
            hwnd = find_window(target_title)
            if hwnd:
                activate_window(hwnd)
                for _ in range(30):
                    if not running: break
                    pyautogui.press('left')
                    time.sleep(0.05)


                for _ in range(30):
                    if not running: break
                    pyautogui.press('right')
                    time.sleep(0.05)
            else:
                print("❌ 창을 찾을 수 없음!")
                time.sleep(2)
        else:
            time.sleep(0.1)


# 현재 시간과 비교
now = datetime.datetime.now()
if now > EXPIRE_DATE:
    sys.exit(1)  # 프로그램 종료
    
def enum_windows_by_title(title):
    """특정 창 제목과 일치하는 핸들을 반환"""
    hwnds = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and title in win32gui.GetWindowText(hwnd):
            hwnds.append(hwnd)
    win32gui.EnumWindows(callback, None)
    return hwnds
console_windows = enum_windows_by_title("multiMatching")

def move_resize_window(hwnd, x, y, width, height):
    """창 위치와 크기 조절"""
    win32gui.MoveWindow(hwnd, x, y, width, height, True)

def set_console_window(x=100, y=100, width=800, height=600):
    # 콘솔 창 핸들 가져오기
    hwnd = win32console.GetConsoleWindow()
    if hwnd:
        win32gui.MoveWindow(hwnd, x, y, width, height, True)

# 실행 시 콘솔 창 조절
move_resize_window(console_windows[0], 0, 0, 240, 500)# 1번
# set_console_window(x=200, y=100, width=1000, height=600)
#고객웹훅
webhook_url = 'https://discord.com/api/webhooks/1392398561307529216/NmUk798H0_A5TxmVfizW7UEX79bnT0uk0RrJYyUuRdaPVQtlksLSwnua5p9PMXnWzmoL'
#x
# webhook_url = 'https://discord.com/api/webhooks/1391740750521171999/Fa7P9Mr91uKW6BwNC-enL5kW63qxD8pP82LMRIuvQ2oYGXTwjmY0m7tnxKjZIJrBY4Lk'
searching = False
paused_until = 0
found_flags = {}  # filename: True/False
characterName = input("캐릭터명 : ")

def capture_fullscreen():
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    return screenshot_bgr

def search_images(screen, image_folder):
    global paused_until, found_flags

    for filename in os.listdir(image_folder):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        template_path = os.path.join(image_folder, filename)

        # 한글 경로 지원
        try:
            file_bytes = np.fromfile(template_path, dtype=np.uint8)
            template = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"⚠️ 이미지 로딩 실패: {filename}, 에러: {e}")
            continue

        if template is None:
            continue

        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # 이미지가 발견된 경우
        if max_val >= 0.8:
            if not found_flags.get(filename, False):
                print(f"✅ 발견됨: {filename} at {max_loc} (유사도: {max_val:.2f})")

                data = {
                    "content": f"{filename} 몬스터 발견, 캐릭터명 : [{characterName}]",
                    "username": characterName
                }
                response = requests.post(webhook_url, json=data)
                if response.status_code == 204:
                    print("✅ 디스코드 메시지 전송")
                else:
                    print(f"❌ 전송 실패: {response.status_code}, {response.text}")
                found_flags[filename] = True  # 발견 상태 기록
                # paused_until = time.time() + 60  # 1분 쉬기
        else:
            # 이미지가 더 이상 화면에 없으면 다시 탐지 가능하게 초기화
            if found_flags.get(filename, False):
                print(f"🔄 {filename} 사라짐, 다시 탐지 가능 상태로 전환")
            found_flags[filename] = False
    return True  # 계속 탐지 루프 돌기 위함

def search_loop():
    global searching, paused_until
    print("🔎 이미지 서치 루프 시작 (F2로 중지 가능)")
    while True:
        if searching:
            screen = capture_fullscreen()
            found = search_images(screen, "images")
            # if not found:
                # print("❌ 이미지 없음. 다시 탐색 중...")
            time.sleep(1)
        else:
            time.sleep(0.1)

def key_listener():
    global searching
    global running
    print("⌨️  F1: 시작 / F2: 중지 / F3: 좌우움직임 / F4: 움직임멈춤")
    while True:
        if keyboard.is_pressed('f1'):
            if not searching:
                print("▶️ 멀티이미지 서치 시작")
                searching = True
            time.sleep(0.3)  # 키 중복 방지
        elif keyboard.is_pressed('f2'):
            if searching:
                print("⏹️ 멀티이미지 서치 중지")
                searching = False
            time.sleep(0.3)
        elif keyboard.is_pressed('f3'):
            if not running:
                running = True
                print("▶️ 자동 이동 시작!")
            time.sleep(0.3)
        elif keyboard.is_pressed('f4'):
            if running:
                running = False
                print("⏹️ 자동 이동 중지!")
            time.sleep(0.3)


if __name__ == "__main__":
    # 이미지 서치 스레드    
    threading.Thread(target=search_loop, daemon=True).start()
    threading.Thread(target=move_loop, daemon=True).start()
    key_listener()
