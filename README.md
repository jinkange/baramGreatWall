pyinstaller --onefile --hidden-import=cv2 multiMatching.py
pyinstaller --onefile --hidden-import=cv2 multiMatchingMove.py

pip install pyautogui keyboard opencv-python pytesseract pillow pygetwindow
pip install easyocr
pip install pynput
