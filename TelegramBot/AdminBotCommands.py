import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from .models import TemporaryDataStorage, Shop


# data = {
#   "user_data": {
#       "bot_user_id": {
#           "new_product": {
#               "message_id": <Int>,  -- id of message which will be edited
#               "name": <String>,
#               "description": <String>,
#               "price": <Decimal>,
#               "tags": <String>,
#           },
#           "new_shop": {
#               "message_id": <int>, -- id of message which will be edited
#               "name": <String>,
#               "token": <String>,
#           },
#           "active_shop": id <int> -- id of the shop
#       },
#   },
#   "functions_waiting_input": {
#       "bot_user_id": "function_name"
#   }
# }
def set_waiting_input_from_user(bot_user, function_name):
    data = TemporaryDataStorage.get_data()
    if "functions_waiting_input" in data.keys():
        data["functions_waiting_input"][str(bot_user.id)] = function_name
    else:    
        data["functions_waiting_input"] = {
            str(bot_user.id): function_name
        }
    TemporaryDataStorage.put_data(data)
    return

def set_new_shop_data(bot_user, field_name, field_value):
    data = TemporaryDataStorage.get_data()
    id = str(bot_user.id)
    if "user_data" not in data.keys(): data["user_data"] = {}
    if id not in data["user_data"].keys(): data["user_data"][id] = {}
    if "new_shop" not in data["user_data"][id].keys(): data["user_data"][id]["new_shop"] = {}
    data["user_data"][id]["new_shop"][field_name] = field_value
    TemporaryDataStorage.put_data(data)
    return

def unknown(*args, **kwargs):
    print("Admin unknown command")
    reply_keyboard = [
        ['/my_shops', '/new_shop']
    ]
    msg = {
        "text": "Unknown command",
        "reply_markup": ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    }
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    telegram_bot.sendMessage(chat_id, **msg)

def new_shop(*args, **kwargs):
    print("new_shop admin command")
    msg = {
        "text": "Adding new shop",
    }
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try: telegram_bot.sendMessage(chat_id, **msg)
    except Exception as e: print(e)
    return new_shop_step_1(*args, **kwargs)

def new_shop_step_1(*args, **kwargs):
    print("new_shop_step_1. Asking for name")
    bot_user = kwargs.get("bot_user")
    set_waiting_input_from_user(bot_user, 'AdminBotCommands.new_shop_step_2')
    msg = {
        "text": "Enter your shop name.\nType \"/cancel\" to abort",
    }
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try: sent_message = telegram_bot.sendMessage(chat_id, **msg)
    except Exception as e: print(e)
    set_new_shop_data(bot_user, 'message_id', sent_message.message_id)
    
def new_shop_step_2(*args, **kwargs):
    print("new_shop_step_2. Saving Name and Asking for Token")
    user_input = kwargs.get("user_input")
    if (user_input in ("cancel", "/cancel")): return new_shop_abort(reason="user cancelled", *args, **kwargs)
    # Saving name
    data = TemporaryDataStorage.get_data()
    bot_user = kwargs.get("bot_user")
    try:
        data["user_data"][str(bot_user.id)]["new_shop"]["name"] = user_input
        TemporaryDataStorage.put_data(data)
        edit_message_id = data['user_data'][str(bot_user.id)]["new_shop"]["message_id"]
        new_shop_name = data['user_data'][str(bot_user.id)]['new_shop']['name']
    except:
        return new_shop_abort(reason = "user_data damaged", *args, **kwargs)
    
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    user_message_id = kwargs.get("message_id")
    try: telegram_bot.delete_message(chat_id, user_message_id)
    except Exception as e: print(e)
    # Asking for token
    set_waiting_input_from_user(bot_user, 'AdminBotCommands.new_shop_step_3')
    msg = {
        "text": f"Name: {new_shop_name}\nEnter your bot token.\nType \"/cancel\" to abort",
    }
    try: telegram_bot.edit_message_text(msg["text"], chat_id, edit_message_id)
    except Exception as e: print(e)
    

def new_shop_step_3(*args, **kwargs):
    print("new_shop_step_3. Saving Token and Asking for Confirmation")
    # Saving token and asking for confiramtion
    user_input = kwargs.get("user_input")
    if (user_input in ("cancel", "/cancel")): return new_shop_abort(reason="user cancelled", *args, **kwargs)
    # Saving token
    bot_user = kwargs.get("bot_user")
    data = TemporaryDataStorage.get_data()
    try:
        data["user_data"][str(bot_user.id)]["new_shop"]["token"] = user_input
        TemporaryDataStorage.put_data(data)
        edit_message_id = data['user_data'][str(bot_user.id)]["new_shop"]["message_id"]
        new_shop_name = data['user_data'][str(bot_user.id)]['new_shop']['name']
        new_shop_token = data['user_data'][str(bot_user.id)]['new_shop']['token']
    except:
        return new_shop_abort(reason = "user_data damaged", *args, **kwargs)
    # clearing waiting input
    data["functions_waiting_input"].pop(str(bot_user.id), None)
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    # deleting user response
    user_message_id = kwargs.get("message_id")
    try:
        telegram_bot.delete_message(chat_id, user_message_id)
    except:
        pass
    # Asking for confirmation
    TemporaryDataStorage.put_data(data)
    msg = {
        "text": f"Name: {new_shop_name}\nToken: {new_shop_token}",
    }
    reply_keyboard = [
        [InlineKeyboardButton(text='Cancel', callback_data=json.dumps({
            "comm": "new_shop_abort",
            "args": {
                "edit_message_id": edit_message_id
            }
        })), 
        InlineKeyboardButton(text='Confirm', callback_data=json.dumps({
            "comm": "new_shop_confirm",
            "args": {
                "edit_message_id": edit_message_id
            }
        }))]
    ]
    try: telegram_bot.edit_message_text(msg["text"], chat_id, edit_message_id)
    except Exception as e: print(e)
    try: telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id, reply_markup=InlineKeyboardMarkup(reply_keyboard))
    except Exception as e: print(e)

def new_shop_abort(reason=None, *args, **kwargs):
    data = TemporaryDataStorage.get_data()
    bot_user = kwargs.get("bot_user")
    # clearing stored user input
    data["user_data"][str(bot_user.id)]["new_shop"] = {}
    # clearing waiting input
    data["functions_waiting_input"].pop(str(bot_user.id), None)
    TemporaryDataStorage.put_data(data)
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try: telegram_bot.sendMessage("new shop creation aborted", chat_id)
    except Exception as e: print(e)


def my_shops(*args, **kwargs):
    bot_user = kwargs.get('bot_user')
    telegram_bot = kwargs.get('telegram_bot')
    chat_id = kwargs.get('chat_id')
    shops = Shop.objects.filter(owner=bot_user)
    shops_count = len(shops)
    msg = {
        "text": "You have no shops. /new_shop to make one",
        "reply_markup": None
    }
    if shops:
        reply_keyboard = []
        for shop in shops:
            reply_keyboard.append([InlineKeyboardButton(text=shop.name, callback_data=json.dumps({
                "comm": "shop_menu",
                "args": {
                    "shop_id": shop.id
                }
            }))])
        msg = {
            "text": f"You have {shops_count} shops:",
            "reply_markup": InlineKeyboardMarkup(reply_keyboard)
        }
    try: telegram_bot.sendMessage(chat_id=chat_id, text=msg["text"], reply_markup=msg["reply_markup"])
    except Exception as e: print(e)


    
