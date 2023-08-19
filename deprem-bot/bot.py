from aiogram import Bot,Dispatcher,executor,types
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup

bot = Bot(token="token-id-buraya-gelecek")

dp= Dispatcher(bot)
#botun görev yapacağı işlemlerin kodları aşağı yazılacaktır


executor.start_polling(dp)
