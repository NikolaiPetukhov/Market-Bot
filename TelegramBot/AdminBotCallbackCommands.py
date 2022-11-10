import json
import telegram

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from django.conf import settings

from . import services
from .models import TemporaryDataStorage, Bot, Shop
from .error import SetWebhookError


def unknown(**kwargs):
    print("Admin unknown callback command")
    return {"text": "unknown command"}


def new_shop_abort(**kwargs):
    print("new_shop_abort")
    answer = {"text": "loading"}
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    edit_message_id = kwargs.get("edit_message_id")
    # clearing stored stored user input
    TemporaryDataStorage.delete_new_shop_data(bot_user)
    # we shouldnt have any inputs expected but lets still delete it
    TemporaryDataStorage.delete_function_waiting_input(bot_user)
    try:
        telegram_bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=edit_message_id
        )
        telegram_bot.sendMessage(chat_id=chat_id, text="New shop creation aborted")
    except Exception as e:
        print(e)
    return answer


def new_shop_confirm(**kwargs):
    print("new_shop_confirm")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    edit_message_id = kwargs.get("edit_message_id")
    answer = {"text": "loading"}
    # We shouldnt have any inputs expected but lets still delete it
    TemporaryDataStorage.delete_function_waiting_input(bot_user)
    # Check if user reached shop limit
    shops_count = Shop.objects.filter(owner=bot_user).count()
    if shops_count > bot_user.max_shops:
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=edit_message_id
            )
            telegram_bot.sendMessage(
                text=f"You can have only {bot_user.max_shops} shops. New shop not created",
                chat_id=chat_id,
            )
        except Exception as e:
            print(e)
        return answer
    # Trying to create new shop
    try:
        data = TemporaryDataStorage.get_new_shop_data(bot_user)
        services.create_new_shop(data, bot_user)
    except KeyError:
        # data damaged
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=edit_message_id
            )
            telegram_bot.sendMessage(
                text="Unable to create new shop. Please, try again", chat_id=chat_id
            )
        except Exception as e:
            print(e)
        return answer
    except (telegram.error.Unauthorized, telegram.error.InvalidToken) as e:
        # invalid token
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=edit_message_id
            )
            telegram_bot.sendMessage(text="Bot not found. Check token", chat_id=chat_id)
        except Exception as e:
            print(e)
        return answer
    except SetWebhookError as e:
        # unable to set webhook
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=edit_message_id
            )
            telegram_bot.sendMessage(
                text="Unable to set webhook. Please try again", chat_id=chat_id
            )
        except Exception as e:
            print(e)
        return answer
    except Exception as e:
        # unexpected error on shop creation
        print(e)
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=edit_message_id
            )
            telegram_bot.sendMessage(
                text="Unable to create new shop. Please, try again", chat_id=chat_id
            )
        except Exception as e:
            print(e)
        return answer
    # Shop created sucessfully
    TemporaryDataStorage.delete_new_shop_data(bot_user)
    reply_keyboard = [["/my_shops", "/new_shop"]]
    msg = {
        "text": "New shop created sucessfully!",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    try:
        telegram_bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=edit_message_id
        )
        telegram_bot.sendMessage(chat_id, **msg)
    except Exception as e:
        print(e)
    return answer


def shop_menu(**kwargs):
    answer = {"text": "loading"}
    bot_user = kwargs.get("bot_user")
    shop_id = kwargs.get("shop_id")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        answer["text"] = "Shop not found"
        return answer
    if shop.owner != bot_user:
        answer["text"] = "Access Denied"
        return answer
    try:
        bot = Bot.objects.get(shop=shop)
    except:
        bot = None
    try:
        reply_markup = [
            [
                InlineKeyboardButton(
                    text="change Name",
                    callback_data=json.dumps(
                        {"comm": "change_name", "args": {"shop_id": shop.id}}
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="change Token",
                    callback_data=json.dumps(
                        {"comm": "change_bot_token", "args": {"shop_id": shop.id}}
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="create/revoke API-Key",
                    callback_data=json.dumps(
                        {"comm": "new_api_key", "args": {"shop_id": shop.id}}
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Delete Shop",
                    callback_data=json.dumps(
                        {"comm": "delete_shop", "args": {"shop_id": shop.id}}
                    ),
                )
            ],
        ]
        msg = {
            "text": f'Name: {shop.name}\nToken: {str(bot.token) if bot else "-"}\nBot Username: {"@"+str(bot.username) if bot else "-"}',
            "reply_markup": InlineKeyboardMarkup(reply_markup),
        }
        telegram_bot.sendMessage(chat_id=chat_id, **msg)
    except Exception as e:
        print(e)
    return answer


def delete_shop(**kwargs):
    answer = {"text": "loading"}
    bot_user = kwargs.get("bot_user")
    shop_id = kwargs.get("shop_id")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        answer["text"] = "Shop not found"
        return answer
    if shop.owner != bot_user:
        answer["text"] = "Access Denied"
        return answer
    reply_keyboard = [
        [
            InlineKeyboardButton(
                text="Cancel",
                callback_data=json.dumps({"comm": "delete_shop_abort", "args": {}}),
            ),
            InlineKeyboardButton(
                text="Confirm",
                callback_data=json.dumps(
                    {"comm": "delete_shop_confirm", "args": {"shop_id": shop_id}}
                ),
            ),
        ]
    ]
    msg = {
        "text": f'Are you shure to delete shop "{shop.name}"?',
        "reply_markup": InlineKeyboardMarkup(reply_keyboard),
    }
    try:
        telegram_bot.sendMessage(chat_id, **msg)
    except Exception as e:
        print(e)
    return answer


def delete_shop_confirm(**kwargs):
    shop_id = kwargs.get("shop_id")
    bot_user = kwargs.get("bot_user")
    message_id = kwargs.get("message_id")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    answer = {"text": "deleting"}
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        answer["text"] = "Shop not found"
        return answer
    if shop.owner != bot_user:
        answer["text"] = "Access Denied"
        return answer
    shop.delete()
    try:
        telegram_bot.edit_message_text(
            text="Shop Deleted!", chat_id=chat_id, message_id=message_id
        )
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)
    return answer


def delete_shop_abort(**kwargs):
    answer = {"text": "aborting.."}
    message_id = kwargs.get("message_id")
    chat_id = kwargs.get("chat_id")
    telegram_bot = kwargs.get("telegram_bot")
    try:
        telegram_bot.edit_message_text(
            text="Aborted", chat_id=chat_id, message_id=message_id
        )
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)
    return answer


def new_api_key(**kwargs):
    answer = {"text": "loading"}
    bot_user = kwargs.get("bot_user")
    shop_id = kwargs.get("shop_id")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        answer["text"] = "Shop not found"
        return answer
    if shop.owner != bot_user:
        answer["text"] = "Access Denied"
        return answer
    reply_keyboard = [
        [
            InlineKeyboardButton(
                text="Cancel",
                callback_data=json.dumps({"comm": "new_api_key_abort", "args": {}}),
            ),
            InlineKeyboardButton(
                text="Confirm",
                callback_data=json.dumps(
                    {"comm": "new_api_key_confirm", "args": {"shop_id": shop_id}}
                ),
            ),
        ]
    ]
    msg = {
        "text": "Are you shure to make new API-Key?",
        "reply_markup": InlineKeyboardMarkup(reply_keyboard),
    }
    try:
        telegram_bot.sendMessage(chat_id, **msg)
    except Exception as e:
        print(e)
    return answer


def new_api_key_confirm(**kwargs):
    answer = {"text": "creating new key.."}
    message_id = kwargs.get("message_id")
    chat_id = kwargs.get("chat_id")
    telegram_bot = kwargs.get("telegram_bot")
    shop_id = kwargs.get("shop_id")
    bot_user = kwargs.get("bot_user")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        answer["text"] = "Shop not found"
        return answer
    if shop.owner != bot_user:
        answer["text"] = "Access Denied"
        return answer
    _, key = shop.revoke_api_key()
    try:
        telegram_bot.edit_message_text(
            text=f"API-Key: {key}", chat_id=chat_id, message_id=message_id
        )
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)
    return answer


def new_api_key_abort(**kwargs):
    answer = {"text": "aborting.."}
    message_id = kwargs.get("message_id")
    chat_id = kwargs.get("chat_id")
    telegram_bot = kwargs.get("telegram_bot")
    try:
        telegram_bot.edit_message_text(
            text="Aborted", chat_id=chat_id, message_id=message_id
        )
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)
    return answer


def change_bot_token(**kwargs):
    answer = {"text": "loading"}
    shop_id = kwargs.get("shop_id")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        answer["text"] = "Shop not found"
        return answer
    if shop.owner != bot_user:
        answer["text"] = "Access Denied"
        return answer
    TemporaryDataStorage.put_new_token_shop_id(bot_user, shop.id)
    TemporaryDataStorage.put_function_waiting_input(
        bot_user, "AdminBotCommands.change_bot_token_confirm"
    )
    reply_keyboard = [["cancel"]]
    msg = {
        "text": "Send new Token",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    telegram_bot.send_message(chat_id, **msg)
    return answer


def change_shop_name(**kwargs):
    answer = {"text": "loading"}
    shop_id = kwargs.get("shop_id")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        answer["text"] = "Shop not found"
        return answer
    if shop.owner != bot_user:
        answer["text"] = "Access Denied"
        return answer
    TemporaryDataStorage.put_new_name_shop_id(bot_user, shop.id)
    TemporaryDataStorage.put_function_waiting_input(
        bot_user, "AdminBotCommands.change_shop_name_confirm"
    )
    reply_keyboard = [["cancel"]]
    msg = {
        "text": "Send new Name",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    telegram_bot.send_message(chat_id, **msg)
    return answer
