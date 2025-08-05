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
key_press_time = 0
char_slot = 0
target_title = "MapleStory Worlds-바람의나라 클래식"
console_keyword  = "baramMoveChannel"


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
    # print("이동성공? : ")
    # print(non_zero_count > threshold)
    return non_zero_count > threshold

def press_key(key):
    global target_title
    global key_press_time
    hwnd = find_window(target_title)
    if hwnd:
        activate_window(hwnd)
        keyboard.press(key)
        time.sleep(key_press_time)
        keyboard.release(key)

def load_move_sequence(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print(f"⚠️ 파일이 비어 있습니다: {json_path}")
                return []
        return json.loads(content)  # or json.load(f) if you reopen
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {json_path}")
        print(f"    → {e}")
        return []

    except Exception as e:
        print(f"❌ 파일을 읽는 중 오류 발생: {json_path}")
        print(f"    → {e}")
        return []

def move_one_step(key):
    press_key(key)

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
        press_key(key)
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
def image_exists_at_region(template_path, region, threshold=0.80):
    """
    template_path: 찾을 이미지 파일 경로
    region: (x, y, width, height)1281 631
    threshold: 일치 정도 (0.0 ~ 1.0)
    """
    screenshot = pyautogui.screenshot(region=region)
    # screenshot = screenshot_all_monitors()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    max_val = np.max(result)
    # print(f"{template_path}찾기 :{max_val}")
    return max_val >= threshold

def match_image(image_name, region, threshold=0.80):
    """
    지정된 이미지와 화면 영역의 스크린샷을 비교해 일치 여부를 반환

    :param image_name: './images/' 안의 이미지 파일 이름 (예: 'player_win.png')
    :param region: (x, y, width, height) 형태의 캡처 좌표
    :param threshold: 일치 기준값 (0~1, 기본값 0.95)
    :return: True (일치) / False (불일치 또는 오류)
    """
    x, y, w, h = region
    region = (x - 10, y - 10, w + 20, h + 20)
    # image_path = os.path.join('./images', image_name)
    # if not os.path.exists(image_path):
    #     print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
    #     return False

    screenshot = pyautogui.screenshot(region=region)
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    template = cv2.imread("./images/"+image_name, cv2.IMREAD_GRAYSCALE)

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    max_val = np.max(result)
    # print(f"{image_name}찾기 :{max_val}")
    return max_val >= threshold

def automation_loop(json_path):
    global result
    global running
    global outside
    check = False
    tempStep = ''
    move_sequence = load_move_sequence(json_path)
    if not move_sequence:  # 리스트가 비어 있다면
        print(f"⚠️ {json_path} 는 내용이 없어 건너뜁니다.")
        return
    region_before = (955, 705, 127, 17)
    region_after = (955, 705, 127, 17)
    while True:
        # 정방향 이동
        if not running:
            time.sleep(1)
            break  # F1 누를 때까지 대기
        
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
                
        if not running:
            break  # 정지 상태이면 역방향 스킵
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
                
        print("✅ 정/역방향 이동 모두 완료.")
        break
    
                
def start_macro():
    global running
    print("▶ 매크로 시작")
    running = True

def stop_macro():
    global running
    print("⏹ 매크로 중지")
    running = False
    
keyboard.add_hotkey('f6', start_macro)
keyboard.add_hotkey('f7', stop_macro)


def run_all_maps():
    if(not running):
        time.sleep(1)
        return
    folder_path = './data'
    json_files = sorted(glob.glob(os.path.join(folder_path, 'mapData.json')))
    if(not json_files):
        print("❌ mapData.json 파일을 찾을 수 없습니다.")
        return
    try:
        with open('./data/server.txt', 'r', encoding='utf-8') as f:
            line = f.read().strip()
            values = [v.strip() for v in line.split(',') if v.strip()]
    except FileNotFoundError:
        print("❌ server.txt 파일을 찾을 수 없습니다.")
        return

    while True:
        if(not running):
            time.sleep(1)
            return
        change = False
        for i, value in enumerate(values):
            if(not running):
                time.sleep(1)
                return
            if(not change):
                for json_path in json_files:
                    print(f"\n📂 {json_path} 실행 대기...")
                    automation_loop(json_path)   
                    if(not running):
                        time.sleep(1)
                        return
                print(f"채널변경 {key_time}초 대기..")
                time.sleep(key_time)
                # print(f"채널변경 전 탭+방향키+엔터 {key_time}회 반복")
                # for i in range(key_time):
                #     press_key('tab')
                #     press_key('right')
                #     press_key('enter')
                #     time.sleep(0.5)
            
            print(f"🔹 채널: {value}")
            #메뉴체크
            time.sleep(1)
            if(not running):
                time.sleep(1)
                return
            region = (126,662, 60, 60)
            if match_image("menuCheck.png", region): 
                pyautogui.click(140,715)
            else:
                print()
            
            #채널클릭
            pyautogui.click(87,451)
            time.sleep(0.1)
            pyautogui.click(87,451)
            if(not running):
                time.sleep(1)
                return
            time.sleep(1)
            #채널 입력창 클릭
            pyautogui.click(870,226)
            time.sleep(0.1)
            pyautogui.click(870,226)
            if(not running):
                time.sleep(1)
                return
            time.sleep(0.5)
            #채널입력
            pyautogui.write(value)
            time.sleep(0.5)
            press_key('enter')
            if(not running):
                time.sleep(1)
                return
            time.sleep(1)
            #검색된채널이없으면?
            region = (580,326,152, 40)
            if match_image("channelNone.png", region): 
                press_key('enter')
                if(not running):
                    time.sleep(1)
                    return
                time.sleep(0.5)
                pyautogui.click(637, 595)
                
                change = True
                continue# 다음채널?
            else:
                pyautogui.click(394,282)
                if(not running):
                    time.sleep(1)
                    return
                time.sleep(1)
                region = (671,329,112,41)
                if match_image("channelSame.png", region): 
                    press_key('enter')
                    time.sleep(0.1)
                    press_key('enter')
                    if(not running):
                        time.sleep(1)
                        return
                    time.sleep(1)
                    pyautogui.click(637, 595)
                    change = True
                    continue# 다음채널?
                else:
                    change = False
                    press_key('enter')
                    time.sleep(0.1)
                    press_key('enter')
                    
                    time.sleep(2)
                    region = (876, 697, 950, 725)
                    if match_image("changecheck.png", region): 
                        print("채널이동 실패")
                        press_key('esc')
                        time.sleep(0.1)
                        press_key('esc')
                        continue# 다음채널?
                        
                    print("채널이동 성공")
                    
            #이어하기
            while True:
                if(not running):
                    time.sleep(1)
                    return
                region = (493, 84, 62, 44)
                if match_image("continue.png", region): 
                    move_and_resize_window("MapleStory Worlds-바람의나라 클래식", 0, 0, 1280,750)
                    move_console_next_to_game("MapleStory Worlds-바람의나라 클래식", console_keyword)
                    pyautogui.click(960,551)
                    pyautogui.click(960,551)
                    break
                else:
                    time.sleep(1)
            
            #선택
            region = (527,179, 100, 48)
            if(not running):
                time.sleep(1)
                return
            if match_image("select.png", region): 
                if(char_slot == 1):
                    pyautogui.click(517,240)
                elif(char_slot == 2):
                    pyautogui.click(517,271)
                elif(char_slot == 3):
                    pyautogui.click(517,300)
                elif(char_slot == 4):
                    pyautogui.click(517,330)
                elif(char_slot == 5):
                    pyautogui.click(517,360)
                pyautogui.click(641,609)
                time.sleep(5)    
            else:
                print()

            
# 시작
def get_valid_number():
    pattern = re.compile(r'^\d+$')  # 0 이상의 정수만 허용

    while True:
        # user_input = input("탭 + 방향키 + 엔터 실행 횟수를 입력하세요: ")
        user_input = input("채널변경 대기시간을 입력하세요: ? 초")
        if pattern.match(user_input):
            number = int(user_input)
            return number
        else:
            print("❌ 0 이상의 정수를 입력해야 합니다.")
def get_valid_number_character():
    pattern = re.compile(r'^\d+$')  # 0 이상의 정수만 허용

    while True:
        user_input = input("선택할 캐릭터 슬롯을 입력하세요: ")
        if pattern.match(user_input) or number < 5:
            number = int(user_input)
            return number
        else:
            print("❌ 1 ~ 4이상의 정수를 입력해야 합니다.")
def get_key_press_time():
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
    char_slot = get_valid_number_character()
    key_press_time = get_key_press_time()
    print("🔄 F6: 시작 | F7: 중지")
    move_and_resize_window("MapleStory Worlds-바람의나라 클래식", 0, 0, 1280,750)
    move_console_next_to_game("MapleStory Worlds-바람의나라 클래식", console_keyword)
    while True:
        run_all_maps()
except Exception as e:
    print(e)
    input("아무키나 누르세요.")
