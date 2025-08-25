pyinstaller --onefile --hidden-import=cv2 multiMatching.py
pyinstaller --onefile --hidden-import=cv2 multiMatchingMove.py


pyinstaller --onefile --hidden-import=cv2 .\baramGreatWall.py
pyinstaller --onefile --hidden-import=cv2 .\baramGreatWallBFS.py
pyinstaller --onefile --hidden-import=cv2 .\moveRecord.py
pyinstaller --onefile --hidden-import=cv2 .\baramMove.py
pyinstaller --onefile --hidden-import=cv2 .\baramMoveChannel.py
pyinstaller --onefile --hidden-import=cv2 .\baramImageTelegram.py

pyinstaller --onefile .\baramStorage.py

pip install pyautogui keyboard opencv-python pytesseract pillow pygetwindow
pip install easyocr
pip install pynput

pip install python-telegram-bot --upgrade