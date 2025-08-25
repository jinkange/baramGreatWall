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
import telegram
import asyncio
EXPIRE_DATE = datetime.datetime(2025, 11, 1)
async def telegram_push(characterName):
    #테스트 내꺼
    token = "8189045932:AAFoSVKDROHgNkAoUB5x6c-XKYErhsqMdh8"
    bot = telegram.Bot(token)

    await bot.send_message(chat_id="8383065560", text=characterName)
    #고객
    # token = "8156775426:AAEVcuU1NDRDAb7hmXX-qSsUd0t5xnpS-3Q"
    # bot = telegram.Bot(token)

    # await bot.send_message(chat_id="7924003109", text="test")
    
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
console_windows = enum_windows_by_title("baramImageTelegram")

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
#고객웹훅 이전고객
# webhook_url = 'https://discord.com/api/webhooks/1392398561307529216/NmUk798H0_A5TxmVfizW7UEX79bnT0uk0RrJYyUuRdaPVQtlksLSwnua5p9PMXnWzmoL'
# #고객웹훅 조재건
# webhook_url = 'https://discord.com/api/webhooks/1396398717611020339/0nLGyT_nBVYjxEL_R3PJnGGjoVUeNwUAOLx3q-rd_O3zJKxci76FP4n11cRUPozypjU-'
def get_matching_rate():
    while True:
        try:
            value = float(input("매칭률(0.00 ~ 1.00 사이) 입력: "))
            
            # 범위 체크
            if 0.0 <= value <= 1.0:
                # 소수점 둘째 자리로 제한
                return round(value, 2)
            else:
                print("❌ 0.00 이상 1.00 이하 숫자만 입력해주세요.")
        
        except ValueError:
            print("❌ 숫자 형식으로 입력해주세요. 예: 0.81")

# 사용 예시
rate = get_matching_rate()
print(f"입력한 매칭률: {rate:.2f}")

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
    global paused_until, found_flags, rate

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
        if max_val >= rate:
            print(f"{filename} 발견!! / 매칭률 : {max_val.toFixed(2)}")
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(telegram_push(characterName))
            return True
    return False

def search_loop():
    global searching, paused_until
    print("🔎 이미지 서치 루프 시작 (F2로 중지 가능)")
    while True:
        if searching:
            screen = capture_fullscreen()
            found = search_images(screen, "images")
            if found:
                print("탐색완료 대기 시작...")
                searching = False
            time.sleep(1)
        else:
            time.sleep(1)

def key_listener():
    global searching
    print("⌨️  F1: 시작(재시작) / F2: 중지")
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

if __name__ == "__main__":
    # 이미지 서치 스레드    
    threading.Thread(target=search_loop, daemon=True).start()
    key_listener()
