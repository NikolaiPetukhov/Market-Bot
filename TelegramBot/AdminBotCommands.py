import json
import telegram

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from .models import TemporaryDataStorage, Shop, Bot


def unknown(*args, **kwargs):
    print("Admin unknown command")
    reply_keyboard = [["/my_shops", "/new_shop"]]
    msg = {
        "text": "Unknown command",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    telegram_bot.sendMessage(chat_id, **msg)


def new_shop(*args, **kwargs):
    print("new_shop admin command")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    bot_user = kwargs.get("bot_user")
    shops = Shop.objects.filter(owner=bot_user)
    if len(shops) >= bot_user.max_shops:
        telegram_bot.sendMessage(chat_id, text="You cant create more shops")
        return
    reply_keyboard = [["cancel"]]
    msg = {
        "text": "Adding new shop",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    try:
        telegram_bot.sendMessage(chat_id, **msg)
    except Exception as e:
        print(e)
    return new_shop_step_1(*args, **kwargs)


def new_shop_step_1(*args, **kwargs):
    print("new_shop_step_1. Asking for name")
    bot_user = kwargs.get("bot_user")
    TemporaryDataStorage.put_function_waiting_input(
        bot_user, "AdminBotCommands.new_shop_step_2"
    )
    msg = {
        "text": "Enter your shop name",
    }
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        sent_message = telegram_bot.sendMessage(chat_id, **msg)
        print(sent_message.message_id)
        TemporaryDataStorage.put_new_shop_data(
            bot_user, "message_id", sent_message.message_id
        )
    except Exception as e:
        print(e)


def new_shop_step_2(*args, **kwargs):
    print("new_shop_step_2. Saving Name and Asking for Token")
    user_input = kwargs.get("user_input")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    user_message_id = kwargs.get("message_id")
    if user_input in ("cancel", "/cancel"):
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        reply_keyboard = [["/my_shops", "/new_shop"]]
        msg = {
            "text": "Aborted",
            "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
        }
        try:
            telegram_bot.sendMessage(chat_id, **msg)
        except Exception as e:
            print(e)
        return
    # Saving name
    TemporaryDataStorage.put_new_shop_data(bot_user, "name", user_input)
    # deleting user response
    try:
        telegram_bot.delete_message(chat_id, user_message_id)
    except Exception as e:
        print(e)
    # Asking for token
    data = TemporaryDataStorage.get_new_shop_data(bot_user)
    print(data)
    try:
        new_shop_name = data["name"]
        edit_message_id = int(data["message_id"])
        print(edit_message_id)
    except Exception as e:
        print(e)
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.sendMessage(
                text="Error ocured. Please, try again", chat_id=chat_id
            )
        except Exception as e:
            print(e)
        return

    TemporaryDataStorage.put_function_waiting_input(
        bot_user, "AdminBotCommands.new_shop_step_3"
    )
    msg = {
        "text": f"Name: {new_shop_name}\nEnter your bot token",
        "chat_id": chat_id,
        "message_id": edit_message_id,
    }
    try:
        telegram_bot.edit_message_text(**msg)
    except Exception as e:
        print(e)


def new_shop_step_3(*args, **kwargs):
    print("new_shop_step_3. Saving Token and Asking for Confirmation")
    # Saving token and asking for confiramtion
    user_input = kwargs.get("user_input")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    user_message_id = kwargs.get("message_id")
    if user_input in ("cancel", "/cancel"):
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        reply_keyboard = [["/my_shops", "/new_shop"]]
        msg = {
            "text": "Aborted",
            "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
        }
        try:
            telegram_bot.sendMessage(chat_id, **msg)
        except Exception as e:
            print(e)
        return
    # Saving token
    TemporaryDataStorage.put_new_shop_data(bot_user, "token", user_input)
    # deleting user response
    try:
        telegram_bot.delete_message(chat_id, user_message_id)
    except Exception as e:
        print(e)

    data = TemporaryDataStorage.get_new_shop_data(bot_user)
    try:
        print(data)
        edit_message_id = int(data["message_id"])
        new_shop_name = data["name"]
        new_shop_token = data["token"]
    except Exception as e:
        print(e)
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.sendMessage(
                text="Error ocured. Please, try again", chat_id=chat_id
            )
        except Exception as e:
            print(e)
        return

    # clearing waiting input
    TemporaryDataStorage.delete_function_waiting_input(bot_user)

    # Asking for confirmation
    msg = {
        "text": f"Name: {new_shop_name}\nToken: {new_shop_token}",
    }
    reply_keyboard = [
        [
            InlineKeyboardButton(
                text="Cancel",
                callback_data=json.dumps(
                    {
                        "comm": "new_shop_abort",
                        "args": {"edit_message_id": edit_message_id},
                    }
                ),
            ),
            InlineKeyboardButton(
                text="Confirm",
                callback_data=json.dumps(
                    {
                        "comm": "new_shop_confirm",
                        "args": {"edit_message_id": edit_message_id},
                    }
                ),
            ),
        ]
    ]
    try:
        telegram_bot.edit_message_text(
            chat_id=chat_id, message_id=edit_message_id, text=msg["text"]
        )
    except Exception as e:
        print(e)
    try:
        telegram_bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=edit_message_id,
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    except Exception as e:
        print(e)


def new_shop_abort(reason=None, *args, **kwargs):
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    # clearing stored user input
    TemporaryDataStorage.delete_new_shop_data(bot_user)
    # clearing waiting input
    TemporaryDataStorage.delete_function_waiting_input(bot_user)
    try:
        telegram_bot.sendMessage("new shop creation aborted", chat_id)
    except Exception as e:
        print(e)


def my_shops(*args, **kwargs):
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    shops = Shop.objects.filter(owner=bot_user)
    shops_count = len(shops)
    msg = {"text": "You have no shops. /new_shop to make one", "reply_markup": None}
    if shops:
        reply_keyboard = []
        for shop in shops:
            reply_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=shop.name,
                        callback_data=json.dumps(
                            {"comm": "shop_menu", "args": {"shop_id": shop.id}}
                        ),
                    )
                ]
            )
        msg = {
            "text": f"You have {shops_count} shops:",
            "reply_markup": InlineKeyboardMarkup(reply_keyboard),
        }
    try:
        telegram_bot.sendMessage(chat_id=chat_id, **msg)
    except Exception as e:
        print(e)


def change_bot_token_confirm(*args, **kwargs):
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    user_input = kwargs.get("user_input")
    if user_input in ("cancel", "/cancel"):
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        TemporaryDataStorage.delete_new_token_shop_id(bot_user)
        reply_keyboard = [["/my_shops", "/new_shop"]]
        msg = {
            "text": "Aborted",
            "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
        }
        try:
            telegram_bot.sendMessage(chat_id, **msg)
        except Exception as e:
            print(e)
        return
    try:
        bot = telegram.Bot(user_input)
        info = bot.get_me()
        print(info)
    except:
        # invalid token
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        TemporaryDataStorage.delete_new_token_shop_id(bot_user)
        try:
            telegram_bot.sendMessage(text="Bot not found. Check token", chat_id=chat_id)
        except Exception as e:
            print(e)
        return
    try:
        shop_id = TemporaryDataStorage.get_new_token_shop_id(bot_user)
        shop = Shop.objects.get(pk=shop_id)
        try:
            old_bot = Bot.objects.get(shop=shop)
            old_bot.delete()
        except:
            pass
        new_bot = Bot.create(token=user_input, shop=shop)
        new_bot.username = info.username
        new_bot.name = info.first_name
        new_bot.save()
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        TemporaryDataStorage.delete_new_token_shop_id(bot_user)
        reply_keyboard = [["/my_shops", "/new_shop"]]
        msg = {
            "text": "Token updated",
            "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
        }
        try:
            telegram_bot.sendMessage(chat_id, **msg)
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)
        # Some other error
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        TemporaryDataStorage.delete_new_token_shop_id(bot_user)
        try:
            telegram_bot.sendMessage(
                text="Error occured. Token not updated", chat_id=chat_id
            )
        except Exception as e:
            print(e)
        raise


def change_shop_name_confirm(*args, **kwargs):
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    user_input = kwargs.get("user_input")
    if user_input in ("cancel", "/cancel"):
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        TemporaryDataStorage.delete_new_name_shop_id(bot_user)
        reply_keyboard = [["/my_shops", "/new_shop"]]
        msg = {
            "text": "Aborted",
            "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
        }
        try:
            telegram_bot.sendMessage(chat_id, **msg)
        except Exception as e:
            print(e)
        return
    try:
        shop_id = TemporaryDataStorage.get_new_name_shop_id(bot_user)
        shop = Shop.objects.get(pk=shop_id)
        shop.name = user_input
        shop.save()
        TemporaryDataStorage.delete_new_name_shop_id(bot_user)
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        reply_keyboard = [["/my_shops", "/new_shop"]]
        msg = {
            "text": "Shop Name updated",
            "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
        }
        try:
            telegram_bot.sendMessage(chat_id, **msg)
        except Exception as e:
            print(e)
    except Exception as e:
        # Some other error
        print(e)
        TemporaryDataStorage.delete_function_waiting_input(bot_user)
        TemporaryDataStorage.delete_new_token_shop_id(bot_user)
        try:
            telegram_bot.sendMessage(
                text="Error occured. Name not updated", chat_id=chat_id
            )
        except Exception as e:
            print(e)
