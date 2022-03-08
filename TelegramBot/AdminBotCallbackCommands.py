from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .models import ShopAPIKey, TemporaryDataStorage, Bot, Shop
import json, telegram
from django.conf import settings

def unknown(**kwargs):
    print("Admin unknown callback command")
    return {
        "text":"unknown command"
    }

def new_shop_abort(**kwargs):
    print("new_shop_abort")
    data = TemporaryDataStorage.get_data()
    bot_user = kwargs.get("bot_user")
    # clearing stored stored user input
    data["user_data"][str(bot_user.id)]["new_shop"] = {}
    # we shouldnt have any inputs expected but lets still delete it
    data["functions_waiting_input"].pop(str(bot_user.id), None)
    TemporaryDataStorage.put_data(data)
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    edit_message_id = kwargs.get("edit_message_id")
    try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
    except Exception as e: print(e)
    try: telegram_bot.sendMessage(text="New shop creation aborted", chat_id=chat_id)
    except Exception as e: print(e)
    ans = {
        "text": "loading"
    }
    return ans

def new_shop_confirm(**kwargs):
    print("new_shop_confirm")
    bot_user = kwargs.get("bot_user")
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    edit_message_id = kwargs.get("edit_message_id")
    data = TemporaryDataStorage.get_data()
    ans = {
        "text": "loading"
    }
    # we shouldnt have any inputs expected but lets still delete it
    data["functions_waiting_input"].pop(str(bot_user.id), None)
    # check if user have less shops than shop limit
    shops_count = Shop.objects.filter(owner=bot_user).count()
    if shops_count > bot_user.max_shops:
        data["user_data"][str(bot_user.id)]["new_shop"] = {}
        TemporaryDataStorage.put_data(data)
        try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
        except Exception as e: print(e)
        try: telegram_bot.sendMessage(text=f"You can have only {bot_user.max_shops} shops. New shop not created", chat_id=chat_id)
        except Exception as e: print(e)
        return ans
    try:
        name = data["user_data"][str(bot_user.id)]['new_shop']["name"]
        token = data["user_data"][str(bot_user.id)]['new_shop']["token"]
        try:
            bot = telegram.Bot(token)
            info = bot.get_me()
        except:
            # invalid token
            data["user_data"][str(bot_user.id)]["new_shop"] = {}
            TemporaryDataStorage.put_data(data)
            try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
            except Exception as e: print(e)
            try: telegram_bot.sendMessage(text="Bot not found. Check token", chat_id=chat_id)
            except Exception as e: print(e)
            return ans
        try:
            my_url = settings.PROJECT_URL
            bot.set_webhook(f'{my_url}/{token}')
        except:
            # unable to set webhook
            data["user_data"][str(bot_user.id)]["new_shop"] = {}
            TemporaryDataStorage.put_data(data)
            try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
            except Exception as e: print(e)
            try: telegram_bot.sendMessage(text="Unable to set webhook. Please try again", chat_id=chat_id)
            except Exception as e: print(e)
            return ans
        shop_obj = Shop.create(name=name, owner=bot_user)
        shop_obj.save()
        bot_obj = Bot(token=token, shop=shop_obj)
        bot_obj.username = info['username']
        bot_obj.name = info['first_name']
        bot_obj.save()
        data["user_data"][str(bot_user.id)]["new_shop"] = {}
        TemporaryDataStorage.put_data(data)
        try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
        except Exception as e: print(e)
        try: telegram_bot.sendMessage(text="New shop created sucessfully!", chat_id=chat_id)
        except Exception as e: print(e)
    except Exception as e:
        print(e)
        data["user_data"][str(bot_user.id)]["new_shop"] = {}
        TemporaryDataStorage.put_data(data)
        try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
        except Exception as e: print(e)
        try: telegram_bot.sendMessage(text="Error ocurred. New shop not created", chat_id=chat_id)
        except Exception as e: print(e)
    return ans

def shop_menu(**kwargs):
    ans = {
        "text": "loading"
    }
    bot_user = kwargs.get('bot_user')
    shop_id = kwargs.get('shop_id')
    telegram_bot = kwargs.get('telegram_bot')
    chat_id = kwargs.get('chat_id')
    shop = Shop.objects.get(pk=shop_id)
    bot = Bot.objects.get(shop=shop)
    if shop.owner != bot_user:
        # access denied
        try: telegram_bot.sendMessage(text="Permission denied", chat_id=chat_id)
        except Exception as e: print(e)
        return ans
    try:
        reply_markup = [
            [InlineKeyboardButton(text="change Name", callback_data=json.dumps({
                "comm": "change_name",
                "args": {
                    "shop_id": shop.id
                }
            }))],
            [InlineKeyboardButton(text="change Token", callback_data=json.dumps({
                "comm": "change_bot_token",
                "args": {
                    "bot_id": bot.id
                }
            }))],
            [InlineKeyboardButton(text="create/revoke API-Key", callback_data=json.dumps({
                "comm": "new_api_key",
                "args": {
                    "shop_id": shop.id
                }
            }))],
            [InlineKeyboardButton(text="Send message to Clients", callback_data=json.dumps({
                "comm": "shout",
                "args": {
                    "shop_id": shop.id
                }
            }))],
            [InlineKeyboardButton(text="Delete Shop", callback_data=json.dumps({
                "comm": "delete_shop",
                "args": {
                    "shop_id": shop.id
                }
            }))]
        ] 
        telegram_bot.sendMessage(text=f"Name: {shop.name}\nToken: {bot.token}\nBot Username: @{bot.username}", 
                                  reply_markup = InlineKeyboardMarkup(reply_markup),
                                  chat_id=chat_id)
    except Exception as e: print(e)
    return ans

def delete_shop(**kwargs):
    shop_id = kwargs.get('shop_id')
    bot_user = kwargs.get('bot_user')
    message_id = kwargs.get('message_id')
    telegram_bot = kwargs.get('telegram_bot')
    chat_id = kwargs.get('chat_id')
    ans = {
        "deleting"
    }
    try: shop = Shop.objects.get(pk=shop_id)
    except:
        telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        return ans
    if shop.owner != bot_user:
        telegram_bot.sendMessage(text="Access Denied", chat_id=chat_id)
        return ans
    shop.delete()
    try: telegram_bot.edit_message_text("Shop Deleted!", chat_id, message_id)
    except Exception as e: print(e)
    try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e: print(e)
    return ans


def new_api_key(**kwargs):
    ans = {
        "text": "loading"
    }
    bot_user = kwargs.get('bot_user')
    shop_id = kwargs.get('shop_id')
    telegram_bot = kwargs.get('telegram_bot')
    chat_id = kwargs.get('chat_id')
    reply_keyboard = [
        [InlineKeyboardButton(text='Confirm', callback_data=json.dumps({
            "comm": "new_api_key_confirm",
            "args": {
                "shop_id": shop_id
            }
        })),
        InlineKeyboardButton(text='Cancel', callback_data=json.dumps({
            "comm": "new_api_key_abort",
            "args": {}
        }))]
    ]
    msg = {
        "text": "Are you shure to make new API-Key?",
        "reply_markup": InlineKeyboardMarkup(reply_keyboard)
    }
    try: telegram_bot.sendMessage(chat_id=chat_id, text=msg["text"], reply_markup=msg["reply_markup"])
    except Exception as e: print(e)
    return ans

def new_api_key_confirm(**kwargs):
    ans = {
        "text": "creating.."
    }
    message_id = kwargs.get('message_id')
    chat_id = kwargs.get('chat_id')
    telegram_bot = kwargs.get('telegram_bot')
    shop_id = kwargs.get('shop_id')
    bot_user = kwargs.get('bot_user')
    try: shop = Shop.objects.get(pk=shop_id)
    except:
        telegram_bot.sendMessage(text="Shop not found", chat_id=chat_id)
        return ans
    if shop.owner != bot_user:
        telegram_bot.sendMessage(text="Access Denied", chat_id=chat_id)
        return ans
    _, key = shop.revoke_api_key()
    try: telegram_bot.edit_message_text(f"API-Key: {key}", chat_id, message_id)
    except Exception as e: print(e)
    try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e: print(e)
    return ans

def new_api_key_abort(**kwargs):
    ans = {
        "text": "aborting.."
    }
    message_id = kwargs.get('message_id')
    chat_id = kwargs.get('chat_id')
    telegram_bot = kwargs.get('telegram_bot')
    try: telegram_bot.edit_message_text("Aborted", chat_id, message_id)
    except Exception as e: print(e)
    try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
    except Exception as e: print(e)
    return ans