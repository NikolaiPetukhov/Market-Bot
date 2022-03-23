import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from .models import Product, Shop


def unknown(*args, **kwargs):
    print("unknown command")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    reply_keyboard = [["🏠Main Menu"]]
    msg = {
        "text": "Unknown command",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    telegram_bot.sendMessage(chat_id, **msg)


def start(*args, **kwargs):
    print("start")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    reply_keyboard = [["🏠Main Menu"]]
    msg = {
        "text": "Start command",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    telegram_bot.sendMessage(chat_id, **msg)


def main_menu(*args, **kwargs):
    print("main_menu")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    shop = kwargs.get("shop")
    reply_keyboard = []
    products = Product.objects.filter(shop=shop)
    for product in products:
        reply_keyboard.append(
            [
                InlineKeyboardButton(
                    text=product.name,
                    callback_data=json.dumps(
                        {"comm": "product", "args": {"id": product.id}}
                    ),
                )
            ]
        )
    msg = {
        "text": shop.welcome_message,
        "reply_markup": InlineKeyboardMarkup(reply_keyboard),
    }
    telegram_bot.sendMessage(chat_id, **msg)
