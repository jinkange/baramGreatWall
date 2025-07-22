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

import time
from collections import deque
to_visit = deque()
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
def check_image_changed(before_img, after_img, threshold=5, typename=''):
    diff = cv2.absdiff(before_img, after_img)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    non_zero_count = cv2.countNonZero(gray)
    print(f"{typename} 찾기 : {non_zero_count > threshold} / 다른픽셀 : {non_zero_count}")
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



def load_move_sequence(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# def move_one_step(key):
#     press_key(key, duration=0.3)

def get_reverse_key(key):
    reverse_map = {
        'up': 'down',
        'down': 'up',
        'left': 'right',
        'right': 'left'
    }
    return reverse_map.get(key, key)



def move_and_verify_step(key, region_before, region_after):
    before = screenshot_region(region_before)
    move_one_step(key)
    after = screenshot_region(region_after)

    if check_image_changed(before, after):
        return True
    else:
        return False

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
    
    # popup_region = (382, 370, 125, 82)
    # popup_image_path = "./images/worldmap.png"  # 비교할 팝업 이미지 경로
        
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
import time

# 기본 방향 설정
directions = {
    'up': ('up', (0, -1)),
    'down': ('down', (0, 1)),
    'left': ('left', (-1, 0)),
    'right': ('right', (1, 0)),
}

def opposite(direction):
    return {
        'up': 'down',
        'down': 'up',
        'left': 'right',
        'right': 'left'
    }[direction]

visited = set()
path = []

# 현재 좌표 (x, y) 와 포탈 방향 (dx, dy)
def mark_portal_block_zone(x, y, dx, dy):
    for i in range(-4, 5):
        if dx != 0:
            blocked_x = x + dx * i
            visited.add((blocked_x, y))
        elif dy != 0:
            blocked_y = y + dy * i
            visited.add((x, blocked_y))
def press_key(key, duration=0.20):
    global target_title
    hwnd = find_window(target_title)
    if hwnd:
        activate_window(hwnd)
        keyboard.press(key)
        time.sleep(duration)
        keyboard.release(key)

def move_one_step(key):
    press_key(key, 0.1)
    time.sleep(0.1)
def mark_portal_area_visited(x, y, dx, dy):
    global visited
    # dx, dy는 이동방향을 나타냄
    if dx != 0:  # 수직 이동 (위아래)
        for i in range(-3, 4):
            visited.add((x + dx, y + dy + i))
            path.append((x + dx, y + dy + i))
    elif dy != 0:  # 수평 이동 (좌우)
        for i in range(-3, 4):
            visited.add((x + dx + i, y + dy))
            path.append((x + dx + i, y + dy))
            
def move_and_verify_step(key):
    region_move = (955, 705, 127, 17)
    region_portal = (417, 36, 131, 20)

    before_move = screenshot_region(region_move)
    before_portal = screenshot_region(region_portal)

    move_one_step(key)

    after_move = screenshot_region(region_move)
    after_portal = screenshot_region(region_portal)

    moved = check_image_changed(before_move, after_move, 5,"이동확인")
    portal_moved = check_image_changed(before_portal, after_portal,5, "포탈확인")

    return moved, portal_moved


def dfs(x, y):
    global result
    global running
    global visited
    if(result == 1):
        return
    
    if (x, y) in visited:
        return
    visited.add((x, y))
    path.append((x, y))  # 이동한 곳만 기록 (복귀 시엔 기록 X)

    for dir_name, (key, (dx, dy)) in directions.items():
        moved, portal_moved = move_and_verify_step(key)
        wallCheck()
        if(result == 1):
            break
        elif(result ==2):
            while(not running):
                time.sleep(1)
                
            
        if moved:
            if portal_moved:
                move_one_step(opposite(key))  # 포탈에서 복귀
                pyautogui.press('esc')
                                # 포탈인 경우: 바로 복귀하고 방문만 표시
                # 현재 위치 재방문 방지
                # visited.add((x, y))
                # 포탈 주변 방문 처리
                # 포탈인 경우: 주변을 to_visit에 추가
                if dx != 0:
                    for i in range(-3, 4):
                        nx, ny = x + dx, y + dy + i
                        if (nx, ny) not in visited:
                            to_visit.append((nx, ny))
                elif dy != 0:
                    for i in range(-3, 4):
                        nx, ny = x + dx + i, y + dy
                        if (nx, ny) not in visited:
                            to_visit.append((nx, ny))
                
                # 이후 dfs 루프 밖에서 처리
                while to_visit:
                    tx, ty = to_visit.popleft()
                    dfs(tx, ty)
            else:
                dfs(x + dx, y + dy)
        
        


def follow_path_loop():
    print("🔁 맵 순환 시작...")
    direction_map = {
        (0, -1): 'up',
        (0, 1): 'down',
        (-1, 0): 'left',
        (1, 0): 'right'
    }

    for i in range(len(path)):
        current = path[i]
        next_ = path[(i + 1) % len(path)]  # 다음 좌표 (무한 루프)

        dx = next_[0] - current[0]
        dy = next_[1] - current[1]

        key = direction_map.get((dx, dy))
        if key:
            move_one_step(key)
        else:
            print(f"⚠️ 경로 오류: {current} -> {next_} 이동 불가 방향")

# 실행 예시
if __name__ == "__main__":
    print("🔍 맵 전체 탐색 시작...")
    move_and_resize_window("MapleStory Worlds-바람의나라 클래식", 0, 0, 1280,750)
    move_console_next_to_game("MapleStory Worlds-바람의나라 클래식", console_keyword)
    print("🔄 F1: 시작 | F2: 중지 | F3: 재시작")
    characterName = input("캐릭터명 : ")
    while(not running):
        time.sleep(1)
                
    dfs(0, 0)  # 시작 위치는 (0, 0) 기준 상대좌표
    print(f"✅ 탐색 완료! 방문 좌표 수: {len(visited)}")
    time.sleep(2)
    follow_path_loop()  # 순환 실행


# # 시작

# print("🔄만리장성2 X:6, Y:97 출발")

# run_all_maps()
