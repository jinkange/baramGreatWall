import telegram
import asyncio
import tkinter as tk
from tkinter import messagebox

async def telegram_push():
    #테스트 내꺼
    token = "8189045932:AAFoSVKDROHgNkAoUB5x6c-XKYErhsqMdh8"
    bot = telegram.Bot(token)

    await bot.send_message(chat_id="8383065560", text="hello")
    #고객
    # token = "8156775426:AAEVcuU1NDRDAb7hmXX-qSsUd0t5xnpS-3Q"
    # bot = telegram.Bot(token)

    # await bot.send_message(chat_id="7924003109", text="test")


root = tk.Tk()
root.withdraw()

# 간단한 확인창
messagebox.showinfo("확인", "작업이 완료되었습니다!")

# 창 닫기
root.destroy()
    
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(telegram_push())

