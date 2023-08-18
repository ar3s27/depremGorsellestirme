from aiogram import Bot,Dispatcher,executor,types
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup

bot = Bot(token="6435260959:AAF_XkKOaCnQ0RMjDS2SzVPiSQcOu3n0TJE")

dp= Dispatcher(bot)
#botun görev yapacağı işlemlerin kodları aşağı yazılacaktır


executor.start_polling(dp)