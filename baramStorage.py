try:
    import pyautogui
    import keyboard
    import time
    import pygetwindow as gw
    import win32gui, win32con
    import win32process
    import win32api
    import pyperclip
    import re
except Exception as e:
    print(e)
    input("아무키나 누르세요...")

result = False
running = False
running2 = False
count = 0
storageCount = 0
outside = False
key_time = 0
target_title = "MapleStory Worlds-바람의나라 클래식"
console_keyword  = "baramStorage"


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
    console_hwnd = find_console_window(console_keyword)
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


def press_key(key):
    global target_title
    hwnd = find_window(target_title)
    if hwnd:
        activate_window(hwnd)
        keyboard.press(key)
        keyboard.release(key)



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
        
def automation_loop():
    global count
    global running
    if not running:
        time.sleep(0.1)
        return
    
    pyautogui.click(86,487)
    time.sleep(0.01)
    pyautogui.click(595,375)
    time.sleep(0.01)
    pyautogui.click(577,310)
    time.sleep(0.01)
    pyautogui.click(504,514)
    time.sleep(0.01)
    pyautogui.click(555,385)
    time.sleep(0.01)
    pyautogui.write(str(count))
    time.sleep(0.01)
    pyautogui.click(510,432)
    time.sleep(0.01)
    
    press_key('esc')
    press_key('esc')
    
    running = False
    print("✅ 작동완료.")
    
    
def storage_loop():
    global storageCount

    global running2
    if not running2:
        time.sleep(0.1)
        return
    for i in range(storageCount):
        press_key('enter')
        time.sleep(0.01)
        pyperclip.copy("빨간시약 10개 줘")
        time.sleep(0.2)

        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.01)
        press_key('enter')
        
        time.sleep(0.01)
        # press_key('enter')
        # time.sleep(0.01)
        pyautogui.click(86,487)
        pyautogui.click(86,487)
        time.sleep(0.01)
        pyautogui.click(589,347)
        pyautogui.click(589,347)
        time.sleep(0.01)
        pyautogui.click(603,308)
        pyautogui.click(603,308)
        time.sleep(0.01)
        pyautogui.click(523,551)
        pyautogui.click(523,551)
        time.sleep(0.01)
        pyautogui.click(555,385)
        pyautogui.click(555,385)
        time.sleep(0.01)
        pyautogui.write("10")
        time.sleep(0.01)
        pyautogui.click(525,438)
        pyautogui.click(525,438)
        time.sleep(0.01)
        pyautogui.click(590,456)
        pyautogui.click(590,456)
        time.sleep(0.01)
        # time.sleep(0.01)
        # pyautogui.click(504,514)
        # time.sleep(0.01)
        # pyautogui.click(555,385)
        # time.sleep(0.01)
        # pyautogui.write(str(count))
        # time.sleep(0.01)
        # pyautogui.click(510,432)
        # time.sleep(0.01)
    
        # press_key('esc')
        # press_key('esc')
    
    running2 = False
    print("✅ 작동완료.")
    
def start_macro():
    global running
    print("▶ 꺼내기 시작")
    running = True
    
def start_macro2():
    global running2
    print("▶ 빨간시약 시작")
    running2 = True
    
keyboard.add_hotkey('f1', start_macro)
keyboard.add_hotkey('f4', start_macro2)

def run_all_maps():
    while True:
        automation_loop()
        storage_loop()
            
# 시작
def get_valid_number():
    pattern = re.compile(r'^\d+$')  # 0 이상의 정수만 허용

    while True:
        user_input = input("꺼낼 갯수를 입력하세요: ")
        if pattern.match(user_input):
            number = int(user_input)
            return number
        else:
            print("❌ 0 이상의 정수를 입력해야 합니다.")

def get_valid_number_storage():
    pattern = re.compile(r'^\d+$')  # 0 이상의 정수만 허용

    while True:
        user_input = input("구매할 횟수를 입력하세요: ")
        if pattern.match(user_input):
            number = int(user_input)
            return number
        else:
            print("❌ 0 이상의 정수를 입력해야 합니다.")
            
try:
    count = get_valid_number()
    storageCount = get_valid_number_storage()
    move_and_resize_window("MapleStory Worlds-바람의나라 클래식", 0, 0, 1280,750)
    move_console_next_to_game("MapleStory Worlds-바람의나라 클래식", console_keyword)
    print("🔄 F1: 꺼내기 / F4: 빨간시약 구매 ")
    run_all_maps()
except Exception as e:
    print(e)
    input("아무키나 누르세요.")
