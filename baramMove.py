try:
    import glob
    import os
    import pyautogui
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
    import re
except Exception as e:
    print(e)
    input("아무키나 누르세요...")

result = False
running = False
outside = False
key_time = 0
target_title = "MapleStory Worlds-바람의나라 클래식"
console_keyword  = "baramMove"


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
    console_hwnd = find_console_window("baramMove")
    move_and_resize_window_by_hwnd(console_hwnd, console_x, console_y, console_width, console_height)

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
    else:
        print(f"{title} 창을 찾을 수 없습니다.")

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

def press_key(key, key_time2):
    print(key_time2)
    global target_title
    hwnd = find_window(target_title)
    if hwnd:
        activate_window(hwnd)
        keyboard.press(key)
        time.sleep(key_time2)
        keyboard.release(key)

def load_move_sequence(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def move_one_step(key, key_time):
    press_key(key, key_time)

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
    global key_time
    detour_keys = {
        'left': ['up', 'left','left', 'down'],
        'right': ['up', 'right','right', 'down'],
        'up': ['left', 'up','up', 'right'],
        'down': ['right', 'down','down', 'left']
    }
    before = screenshot_region(region_before)
    for key in detour_keys.get(last_key, []):
        press_key(key, key_time)
    after = screenshot_region(region_after)
    if check_image_changed(before, after):
        # print(f"✅ {key} 방향 우회 성공")
        return False
    else:
        outside = True
    # print("⛔ 모든 우회 실패 → 벽 판단")
        return False
    


def move_and_verify_step(key, region_before, region_after):
    global key_time
    before = screenshot_region(region_before)
    move_one_step(key, key_time)
    after = screenshot_region(region_after)

    if check_image_changed(before, after):
        return True
    return try_detour(key, region_before, region_after)

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
            
            success = move_and_verify_step(key, region_before, region_after)
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
            
            success = move_and_verify_step(key, region_before, region_after)
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
            print(f"\n📂 {json_path} 실행 대기...")
            automation_loop(json_path)
            if result == 1:
                break
            if result == 3:
                break
        if result == 1:
                break
            
# 시작
def get_valid_number():
    pattern = re.compile(r'^\d+(\.\d{1,2})?$')  # 정수 또는 소수점 둘째자리까지 허용

    while True:
        user_input = input("키입력 시간을 입력하세요. (최대 소수점 둘째자리): ")
        if pattern.match(user_input):
            number = float(user_input)
            if number >= 0:
                return number
            else:
                print("❌ 0 이상의 값을 입력해야 합니다.")
        else:
            print("❌ 잘못된 형식입니다. 예: 3, 3.1, 3.14")

try:
    key_time = get_valid_number()
    move_and_resize_window("MapleStory Worlds-바람의나라 클래식", 0, 0, 1280,750)
    move_console_next_to_game("MapleStory Worlds-바람의나라 클래식", console_keyword)
    print("🔄 F1: 시작 | F2: 중지 | F3: 재시작")
    run_all_maps()
except Exception as e:
    print(e)
    input("아무키나 누르세요.")
