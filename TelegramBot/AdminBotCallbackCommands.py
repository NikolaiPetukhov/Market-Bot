import json
import telegram

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from django.conf import settings

from .models import TemporaryDataStorage, Bot, Shop


def unknown(**kwargs):
    print("Admin unknown callback command")
    return {"text": "unknown command"}


def new_shop_abort(**kwargs):
    print("new_shop_abort")
    ans = {"text": "loading"}
    bot_user = kwargs.get("bot_user")
    # clearing stored stored user input
    TemporaryDataStorage.delete_new_shop_data(bot_user)
    # we shouldnt have any inputs expected but lets still delete it
    TemporaryDataStorage.delete_function_waiting_input(bot_user)
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    edit_message_id = kwargs.get("edit_message_id")
    try:
        telegram_bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=edit_message_id
        )
    except Exception as e:
        print(e)
    try:
        telegram_bot.sendMessage(chat_id=chat_id, text="New shop creation aborted")
    except Exception as e:
        print(e)
    return ans


def new_shop_confirm(**kwargs):
    print("new_shop_confirm")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    edit_message_id = kwargs.get("edit_message_id")
    ans = {"text": "loading"}
    # we shouldnt have any inputs expected but lets still delete it
    TemporaryDataStorage.delete_function_waiting_input(bot_user)
    # check if user have less shops than shop limit
    shops_count = Shop.objects.filter(owner=bot_user).count()
    if shops_count > bot_user.max_shops:
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=edit_message_id
            )
        except Exception as e:
            print(e)
        try:
            telegram_bot.sendMessage(
                text=f"You can have only {bot_user.max_shops} shops. New shop not created",
                chat_id=chat_id,
            )
        except Exception as e:
            print(e)
        return ans
    try:
        # Trying to create new shop
        data = TemporaryDataStorage.get_new_shop_data(bot_user)
        try:
            name = data["name"]
            token = data["token"]
        except:
            # data damaged
            TemporaryDataStorage.delete_new_shop_data(bot_user)
            try:
                telegram_bot.edit_message_reply_markup(
                    chat_id=chat_id, message_id=edit_message_id
                )
            except Exception as e:
                print(e)
            try:
                telegram_bot.sendMessage(
                    text="Unable to create new shop. Please, try again", chat_id=chat_id
                )
            except Exception as e:
                print(e)
            return ans
        try:
            bot = telegram.Bot(token)
            info = bot.get_me()
            print(info)
            print(type(info))
        except:
            # invalid token
            TemporaryDataStorage.delete_new_shop_data(bot_user)
            try:
                telegram_bot.edit_message_reply_markup(
                    chat_id=chat_id, message_id=edit_message_id
                )
            except Exception as e:
                print(e)
            try:
                telegram_bot.sendMessage(
                    text="Bot not found. Check token", chat_id=chat_id
                )
            except Exception as e:
                print(e)
            return ans
        try:
            my_url = settings.PROJECT_URL
            bot.set_webhook(f"{my_url}/{token}")
        except:
            # unable to set webhook
            TemporaryDataStorage.delete_new_shop_data(bot_user)
            try:
                telegram_bot.edit_message_reply_markup(
                    chat_id=chat_id, message_id=edit_message_id
                )
            except Exception as e:
                print(e)
            try:
                telegram_bot.sendMessage(
                    text="Unable to set webhook. Please try again", chat_id=chat_id
                )
            except Exception as e:
                print(e)
            return ans
        shop_obj = Shop.create(name=name, owner=bot_user)
        bot_obj = Bot.create(
            token=token, shop=shop_obj, username=info.username, name=info.first_name
        )
        print(bot_obj)
        shop_obj.save()
        bot_obj.save()
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
        except Exception as e:
            print(e)
        try:
            telegram_bot.sendMessage(chat_id, **msg)
        except Exception as e:
            print(e)
    except Exception as e:
        # Somethig else gone wrong
        print(e)
        TemporaryDataStorage.delete_new_shop_data(bot_user)
        try:
            telegram_bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=edit_message_id
            )
        except Exception as e:
            print(e)
        try:
            telegram_bot.sendMessage(
                text="Unable to create new shop. Please, try again", chat_id=chat_id
            )
        except Exception as e:
            print(e)
        raise
    return ans


def shop_menu(**kwargs):
    ans = {"text": "loading"}
    bot_user = kwargs.get("bot_user")
    shop_id = kwargs.get("shop_id")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        try:
            telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        except Exception as e:
            print(e)
        return ans
    try:
        bot = Bot.objects.get(shop=shop)
    except:
        bot = None
    if shop.owner != bot_user:
        # access denied
        try:
            telegram_bot.sendMessage(text="Permission denied", chat_id=chat_id)
        except Exception as e:
            print(e)
        return ans
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
    return ans


def delete_shop(**kwargs):
    ans = {"text": "loading"}
    shop_id = kwargs.get("shop_id")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        return ans
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
    return ans


def delete_shop_confirm(**kwargs):
    shop_id = kwargs.get("shop_id")
    bot_user = kwargs.get("bot_user")
    message_id = kwargs.get("message_id")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    ans = {"text": "deleting"}
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        return ans
    if shop.owner != bot_user:
        telegram_bot.sendMessage(text="Access Denied", chat_id=chat_id)
        return ans
    shop.delete()
    try:
        telegram_bot.edit_message_text(
            text="Shop Deleted!", chat_id=chat_id, message_id=message_id
        )
    except Exception as e:
        print(e)
    try:
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)
    return ans


def delete_shop_abort(**kwargs):
    ans = {"text": "aborting.."}
    message_id = kwargs.get("message_id")
    chat_id = kwargs.get("chat_id")
    telegram_bot = kwargs.get("telegram_bot")
    try:
        telegram_bot.edit_message_text(
            text="Aborted", chat_id=chat_id, message_id=message_id
        )
    except Exception as e:
        print(e)
    try:
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)
    return ans


def new_api_key(**kwargs):
    ans = {"text": "loading"}
    shop_id = kwargs.get("shop_id")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        return ans
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
    return ans


def new_api_key_confirm(**kwargs):
    ans = {"text": "creating.."}
    message_id = kwargs.get("message_id")
    chat_id = kwargs.get("chat_id")
    telegram_bot = kwargs.get("telegram_bot")
    shop_id = kwargs.get("shop_id")
    bot_user = kwargs.get("bot_user")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        return ans
    if shop.owner != bot_user:
        telegram_bot.sendMessage(text="Access Denied", chat_id=chat_id)
        return ans
    _, key = shop.revoke_api_key()
    try:
        telegram_bot.edit_message_text(
            text=f"API-Key: {key}", chat_id=chat_id, message_id=message_id
        )
    except Exception as e:
        print(e)
    try:
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)
    return ans


def new_api_key_abort(**kwargs):
    ans = {"text": "aborting.."}
    message_id = kwargs.get("message_id")
    chat_id = kwargs.get("chat_id")
    telegram_bot = kwargs.get("telegram_bot")
    try:
        telegram_bot.edit_message_text(
            text="Aborted", chat_id=chat_id, message_id=message_id
        )
    except Exception as e:
        print(e)
    try:
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)
    return ans


def change_bot_token(**kwargs):
    ans = {"text": "loading"}
    shop_id = kwargs.get("shop_id")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        return ans
    if shop.owner != bot_user:
        ans = {"text": "Access Denied"}
        return ans
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
    return ans


def change_shop_name(**kwargs):
    ans = {"text": "loading"}
    shop_id = kwargs.get("shop_id")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        shop = Shop.objects.get(pk=shop_id)
    except:
        telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        return ans
    if shop.owner != bot_user:
        ans = {"text": "Access Denied"}
        return ans
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
    return ans
