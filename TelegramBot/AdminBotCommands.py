import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from .models import TemporaryDataStorage


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

def set_new_shop(bot_user, message_id):
    data = TemporaryDataStorage.get_data()
    if "user_data" in data.keys():
        if str(bot_user.id) in data["user_data"].keys():
            data["user_data"][str(bot_user.id)]["new_shop"] = {
                "message_id": str(message_id)
            }
        else:
            data["user_data"][str(bot_user.id)] = {
                "new_shop": {
                    "message_id": str(message_id)
                }
            }
    else:
        data["user_data"] = {
            str(bot_user.id): {
                "new_shop": {
                    "message_id": str(message_id)
                }
            }
        }
    TemporaryDataStorage.put_data(data)
    return

def unknown(*args, **kwargs):
    print("Admin unknown command")
    reply_keyboard = [
        ['/menu', '/new_product', '/admin']
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
    telegram_bot.sendMessage(chat_id, **msg)
    return new_shop_step_1(*args, **kwargs)

def new_shop_step_1(*args, **kwargs):
    print("new_shop_step_1. Asking for name")
    bot_user = kwargs.get("bot_user")
    set_waiting_input_from_user(bot_user, 'AdminBotCommands.new_shop_step_2')
    msg = {
        "text": "Enter your shop name.\nType \"/cancel\" or \"cancel\" to abort",
    }
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    sent_message = telegram_bot.sendMessage(chat_id, **msg)
    set_new_shop(bot_user, sent_message.message_id)
    

def new_shop_step_2(*args, **kwargs):
    print("new_shop_step_2. Saving Name and Asking for Token")
    user_input = kwargs.get("user_input")
    if (user_input in ("cancel", "/cancel")): return new_shop_abort(reason="user cancelled", *args, **kwargs)
    # Saving name
    bot_user = kwargs.get("bot_user")
    try:
        data = TemporaryDataStorage.get_data()
        data["user_data"][str(bot_user.id)]["new_shop"]["name"] = user_input
        TemporaryDataStorage.put_data(data)
    except:
        return new_shop_abort(reason = "user_data damaged", *args, **kwargs)
    
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        data = TemporaryDataStorage.get_data()
        edit_message_id = data['user_data'][str(bot_user.id)]["new_shop"]["message_id"]
        new_shop_name = data['user_data'][str(bot_user.id)]['new_shop']['name']
    except:
        return new_shop_abort(reason="user_data damaged", *args, **kwargs)
    user_message_id = kwargs.get("message_id")
    try:
        telegram_bot.delete_message(chat_id, user_message_id)
    except:
        pass
    
    # Asking for token
    set_waiting_input_from_user(bot_user, 'AdminBotCommands.new_shop_step_3')
    msg = {
        "text": f"Name: {new_shop_name}\nEnter your bot token.\nType \"/cancel\" or \"cancel\" to abort",
    }
    telegram_bot.edit_message_text(msg["text"], chat_id, edit_message_id)
    

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
    except:
        return new_shop_abort(reason = "user_data damaged", *args, **kwargs)
    
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        edit_message_id = data['user_data'][str(bot_user.id)]["new_shop"]["message_id"]
        new_shop_name = data['user_data'][str(bot_user.id)]['new_shop']['name']
        new_shop_token = data['user_data'][str(bot_user.id)]['new_shop']['token']
    except:
        return new_shop_abort(reason="user_data damaged", *args, **kwargs)
    user_message_id = kwargs.get("message_id")
    try:
        telegram_bot.delete_message(chat_id, user_message_id)
    except:
        pass
    # Asking for confirmation
    del data['functions_waiting_input'][str(bot_user.id)]
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
    try:
        telegram_bot.edit_message_text(msg["text"], chat_id, edit_message_id)
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id, reply_markup=InlineKeyboardMarkup(reply_keyboard))
    except Exception as e:
        print(e)

def new_shop_abort(reason=None, *args, **kwargs):
    data = TemporaryDataStorage.get_data()
    bot_user = kwargs.get("bot_user")
    data["user_data"][str(bot_user.id)]["new_shop"] = {}
    del data["functions_waiting_input"][str(bot_user.id)]
    TemporaryDataStorage.put_data(data)
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    try:
        telegram_bot.sendMessage("new shop creation aborted", chat_id)
    except Exception as e:
        print(e)