import glob
import os
import pyautogui
import easyocr
import keyboard
import time
import numpy as np
from PIL import ImageGrab
import cv2
import json
import pygetwindow as gw
import win32gui, win32con
import win32process
import win32api
import requests
import re


webhook_url = 'https://discord.com/api/webhooks/1396398717611020339/0nLGyT_nBVYjxEL_R3PJnGGjoVUeNwUAOLx3q-rd_O3zJKxci76FP4n11cRUPozypjU-'
result = False
running = False
outside = False
reader = easyocr.Reader(['ko', 'en'], gpu=False)
target_title = "MapleStory Worlds-바람의나라 클래식"
console_keyword  = "baramGreatWall"


def find_console_window(title_contains):
    target_hwnd = None

    def enum_handler(hwnd, _):
        nonlocal target_hwnd
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            if title_contains.lower() in title.lower() and class_name == "ConsoleWindowClass":
                target_hwnd = hwnd

    win32gui.EnumWindows(enum_handler, None)
    return target_hwnd

def move_and_resize_window_by_hwnd(hwnd, x, y, width, height):
    if hwnd:
        win32gui.SetWindowPos(hwnd, None, x, y, width, height, win32con.SWP_NOZORDER)

def find_hwnd_by_title_contains(keyword):
    hwnd = None

    def enum_handler(h, _):
        nonlocal hwnd
        if win32gui.IsWindowVisible(h):
            title = win32gui.GetWindowText(h)
            if keyword.lower() in title.lower():
                hwnd = h

    win32gui.EnumWindows(enum_handler, None)
    return hwnd

def move_console_next_to_game(game_title, console_keyword):
    game_windows = gw.getWindowsWithTitle(game_title)
    if not game_windows:
        print("게임 창을 찾을 수 없습니다.")
        return

    game_win = game_windows[0]
    gx, gy = game_win.left, game_win.top
    gwidth, gheight = game_win.width, game_win.height

    # 콘솔창 찾기
    console_hwnd = find_hwnd_by_title_contains(console_keyword)
    if console_hwnd is None:
        print("콘솔창을 찾을 수 없습니다.")
        return

    # 콘솔창 크기 설정 (게임창 높이에 맞추고 너비는 400 정도)
    console_width = 450
    console_height = gheight
    console_x = gx + gwidth  # 게임 창 오른쪽에 붙이기
    console_y = gy
    console_hwnd = find_console_window("baramGreatWall")
    move_and_resize_window_by_hwnd(console_hwnd, console_x, console_y, console_width, console_height)
    # win32gui.SetWindowPos(
    #     console_hwnd,
    #     None,
    #     console_x, console_y,
    #     console_width, console_height,
    #     win32con.SWP_NOZORDER
    # )



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

def move_and_resize_window(title, x, y, width, height):
    window = gw.getWindowsWithTitle(title)
    if window:
        hwnd = window[0]._hWnd
        win32gui.SetWindowPos(hwnd, None, x, y, width, height, win32con.SWP_NOZORDER)

def play_keys_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        actions = json.load(f)

    base = actions[0][1]
    for key, t in actions:
        time.sleep(t - base)
        keyboard.press_and_release(key)
        base = t

def is_popup_visible(region, template_path, threshold=0.8):
    """
    region: (x, y, width, height)
    template_path: 확인할 이미지 파일 경로 (팝업 이미지)
    """
    screenshot = screenshot_region(region)
    screenshot_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    return max_val >= threshold


def screenshot_region(region):
    x, y, w, h = region
    bbox = (x, y, x + w, y + h)
    img = ImageGrab.grab(bbox)
    return np.array(img)

# 이미지 변화 감지 (True면 바뀐 것)
def check_image_changed(before_img, after_img, threshold=5):
    diff = cv2.absdiff(before_img, after_img)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    non_zero_count = cv2.countNonZero(gray)
    return non_zero_count > threshold


def check_text_in_region(region, keywords):
    img = screenshot_region(region)
    result = reader.readtext(img, detail=0)
    return any(any(keyword in line for keyword in keywords) for line in result)


def check_number_with_context(region, context_keyword, min_value=200):
    img = screenshot_region(region)
    lines = reader.readtext(img, detail=0)

    for line in lines:
        # OCR 결과에서 context_keyword 포함된 줄만 처리
        if context_keyword in line:
            # "숫자+번" 패턴 추출
            matches = re.findall(r'(\d+)번', line)
            for num_str in matches:
                number = int(num_str)
                if number >= min_value:
                    return True
    return False


def press_key(key, duration=0.20):
    global target_title
    hwnd = find_window(target_title)
    if hwnd:
        activate_window(hwnd)
        keyboard.press(key)
        time.sleep(duration)
        keyboard.release(key)

def load_move_sequence(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def move_one_step(key):
    press_key(key, duration=0.20)

def get_reverse_key(key):
    reverse_map = {
        'up': 'down',
        'down': 'up',
        'left': 'right',
        'right': 'left'
    }
    return reverse_map.get(key, key)

def try_detour(last_key, region_before, region_after):
    global outside
    detour_keys = {
        'left': ['up', 'left','left', 'down'],
        'right': ['up', 'right','right', 'down'],
        'up': ['left', 'up','up', 'right'],
        'down': ['right', 'down','down', 'left']
    }
    before = screenshot_region(region_before)
    for key in detour_keys.get(last_key, []):
        press_key(key, duration=0.05)
    after = screenshot_region(region_after)
    if check_image_changed(before, after):
        # print(f"✅ {key} 방향 우회 성공")
        return False
    else:
        outside = True
    # print("⛔ 모든 우회 실패 → 벽 판단")
        return False
    


def move_and_verify_step(key, region_before, region_after):
    before = screenshot_region(region_before)
    move_one_step(key)
    after = screenshot_region(region_after)

    if check_image_changed(before, after):
        return True

    # print(f"⚠️ {key} 이동 실패 → 1초 누르기")
    # press_key(key, duration=1.0)
    # after = screenshot_region(region_after)

    # if check_image_changed(before, after):
        # print(f"✅ {key} 이동 성공 (1초 눌림)")
        # return True

    # print(f"⚠️ 2차 실패 → 우회 시도")
    return try_detour(key, region_before, region_after)

def send_discord_message(message):
    global webhook_url
    # 실제 Discord Webhook 연동 시 구현 필요
    data = {
        "content": f"{message}",
        "username": "baramGreatWall"
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print("✅ 디스코드 메시지 전송")
    else:
        print(f"❌ 전송 실패: {response.status_code}, {response.text}")
    print(f"[디스코드] {message}")

def activate_window(hwnd):
    if hwnd:
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # 현재 쓰레드 ID와 대상 윈도우 쓰레드 ID 연결
            fg_window = win32gui.GetForegroundWindow()
            current_thread = win32api.GetCurrentThreadId()
            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
            fg_thread, _ = win32process.GetWindowThreadProcessId(fg_window)

            win32process.AttachThreadInput(current_thread, target_thread, True)
            win32process.AttachThreadInput(current_thread, fg_thread, True)

        
            win32gui.SetForegroundWindow(hwnd)

            # 다시 연결 해제
            win32process.AttachThreadInput(current_thread, target_thread, False)
            win32process.AttachThreadInput(current_thread, fg_thread, False)
        except Exception as e:
            print(f"⚠️ SetForegroundWindow 실패: {e}")

        time.sleep(0.2)
        

def automation_loop(json_path):
    global result
    global running
    global outside
    check = False
    tempStep = ''
    move_sequence = load_move_sequence(json_path)
    print(f"🔄 {json_path} 이동 시작")
    region_before = (955, 705, 127, 17)
    region_after = (955, 705, 127, 17)
    while True:
        # 정방향 이동
        if(result == 1 or result == 3):
            break
        if not running:
            time.sleep(1)
            continue  # F1 누를 때까지 대기
        
        for step in move_sequence:
            if not running:
                break
            key = step[0]
            if(check):
                if(outside):
                    if (tempStep == key):
                        continue
                    else:
                        outside = False
                        check = False
                else:
                    check = False
                    if (tempStep == key):
                        continue
            
            wallCheck()    
            success = move_and_verify_step(key, region_before, region_after)
            wallCheck()    
            if(not success):
                # 우회시도
                check = True
                tempStep = key
                
            
            if(result == 1):
                break
            elif(result == 2):
                stop_macro()
                break
            elif(result == 3):
                break
        if(result == 1 or result == 3):
            break
        if not running:
            continue  # 정지 상태이면 역방향 스킵
        print("🔁 역방향 복귀 시작")
        # 역방향 이동
        for step in reversed(move_sequence):
            if not running:
                break
            key = get_reverse_key(step[0])
            if(check):
                if(outside):
                    if (tempStep == key):
                        continue
                    else:
                        outside = False
                        check = False
                else:
                    check = False
                    if (tempStep == key):
                        continue
            
            wallCheck()    
            success = move_and_verify_step(key, region_before, region_after)
            wallCheck()    
            if(not success):
                # 우회시도
                check = True
                tempStep = key
                
            
            if(result == 1):
                break
            elif(result == 2):
                stop_macro()
                break
            elif(result == 3):
                break
        print("✅ 정/역방향 이동 모두 완료.")
    
    if(result == 1):
        print("✅ 매크로 종료.")

def automation_away(json_path):
    global result
    global running
    global outside
    check = False
    tempStep = ''
    move_sequence = load_move_sequence(json_path)
    print(f"🔄 {json_path} 이동 시작")
    region_before = (955, 705, 127, 17)
    region_after = (955, 705, 127, 17)
    
    while True:
        # 정방향 이동
        if(result == 1):
            break
        if not running:
            time.sleep(1)
            continue  # F1 누를 때까지 대기
        
        for step in move_sequence:
            if not running:
                break
            key = step[0]
            if(check):
                if(outside):
                    if (tempStep == key):
                        continue
                    else:
                        outside = False
                        check = False
                else:
                    check = False
                    if (tempStep == key):
                        continue
            
            wallCheck()    
            success = move_and_verify_step(key, region_before, region_after)
            wallCheck()    
            if(not success):
                # 우회시도
                check = True
                tempStep = key
                
            if(result == 1):
                break
            elif(result == 2):
                stop_macro()
                break
            elif(result == 3):
                break
        if(result == 1):
            break
        if not running:
            continue  # 정지 상태이면 역방향 스킵
        break
    
    if(result == 1):
        print("✅ 매크로 종료.")
        
                
def wallCheck():
    global result
    popup_region = (456, 218, 209, 50)
    popup_image_path = "./images/popup.png"  # 비교할 팝업 이미지 경로
    if is_popup_visible(popup_region, popup_image_path):
        #팝업닫기
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.3)
        pyautogui.press('enter')
        #
        time.sleep(0.3)
        pyautogui.press('s')
        time.sleep(0.3)
        pyautogui.click(1025, 440)
        time.sleep(0.3)
        pyautogui.click(1025, 440)
        time.sleep(0.3)
        target_text_region = (834, 101, 213, 294)
        keyword = "200"
        if check_number_with_context(target_text_region, "만리장성", 200):
            send_discord_message(f"{characterName} : 만리장성 200회 이상 클리어! 매크로 중지")
            result = 1
        else:
            
            target_text_region = (834, 101, 213, 294)
            keyword = ["벽돌 2개", "벽돌 1개"]
            pyautogui.press('i')
            time.sleep(0.1)
            pyautogui.click(915, 450)
            time.sleep(0.1)
            if check_text_in_region(target_text_region, keyword):
                send_discord_message(f"{characterName} : 벽돌 갯수 2개, 매크로 중지. F3 : 이어하기")
                result = 2
    
    popup_region = (382, 370, 125, 82)
    popup_image_path = "./images/worldmap.png"  # 비교할 팝업 이미지 경로
    if is_popup_visible(popup_region, popup_image_path):
        pyautogui.press('esc')
        time.sleep(1)
        print("월드맵 확인. 초기상태로 되돌아가기")
        # send_discord_message(f"{characterName} : 월드맵 확인, 매크로 중지. F3 : 이어하기")
        result = 3
def start_macro():
    global running
    print("▶ 매크로 시작")
    running = True

def stop_macro():
    global running
    print("⏹ 매크로 중지")
    running = False

def restart_macro():
    global running
    global result
    result = 0
    print("▶ 매크로 재시작")
    running = True
    
keyboard.add_hotkey('f1', start_macro)
keyboard.add_hotkey('f2', stop_macro)
keyboard.add_hotkey('f3', restart_macro)

def run_all_maps():
    global result
    folder_path = './data'
    json_files = sorted(glob.glob(os.path.join(folder_path, 'mapData*.json')))

    while True:
        for json_path in json_files:
            print(f"\n📂 {json_path} 실행 중...")
            automation_loop(json_path)
            if result == 1:
                break
            if result == 3:
                automation_away('./data/worldMapData.json')
                break
        if result == 1:
                break
            
# 시작
move_and_resize_window("MapleStory Worlds-바람의나라 클래식", 0, 0, 1280,750)
move_console_next_to_game("MapleStory Worlds-바람의나라 클래식", console_keyword)
characterName = input("캐릭터명 : ")
print("🔄만리장성2 X:6, Y:97 출발")
print("🔄 F1: 시작 | F2: 중지 | F3: 재시작")
run_all_maps()
