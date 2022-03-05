from telegram import ReplyKeyboardMarkup

def unknown(*args, **kwargs):
    print("Admin unknown command")
    reply_keyboard = [
        ['/start']
    ]
    msg = {
        "text": "Unknown command",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    telegram_bot.sendMessage(chat_id, **msg)

def start(*args, **kwargs):
    print('start')
    reply_keyboard = [
        ['/start']
    ]
    msg = {
        "text": "Start command",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    telegram_bot.sendMessage(chat_id, **msg)
