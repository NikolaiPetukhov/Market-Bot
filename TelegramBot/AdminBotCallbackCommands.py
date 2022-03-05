from .models import TemporaryDataStorage, Bot, Shop

def unknown(**kwargs):
    print("Admin unknown callback command")
    return "unknown"

def new_shop_abort(**kwargs):
    print("new_shop_abort")
    print(kwargs)
    data = TemporaryDataStorage.get_data()
    bot_user = kwargs.get("bot_user")
    data["user_data"][str(bot_user.id)]["new_shop"] = {}
    TemporaryDataStorage.put_data(data)
    telegram_bot = kwargs.get("telegram_bot")
    chat_id = kwargs.get("chat_id")
    print(chat_id)
    edit_message_id = kwargs.get("edit_message_id")
    try:
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
        telegram_bot.sendMessage(text="New shop creation aborted", chat_id=chat_id)
    except Exception as e:
        print(e)
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
    try:
        name = data["user_data"][str(bot_user.id)]['new_shop']["name"]
        token = data["user_data"][str(bot_user.id)]['new_shop']["token"]
        shop_obj = Shop(name=name, owner=bot_user)
        shop_obj.save()
        bot_obj = Bot(token=token, shop=shop_obj)
        bot_obj.save()
        data["user_data"][str(bot_user.id)]["new_shop"] = {}
        TemporaryDataStorage.put_data(data)
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
        telegram_bot.sendMessage(text="New shop created sucessfully!", chat_id=chat_id)
    except Exception as e:
        print(e)
        data["user_data"][str(bot_user.id)]["new_shop"] = {}
        TemporaryDataStorage.put_data(data)
        telegram_bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message_id)
        telegram_bot.sendMessage(text="Error ocurred. New shop not created", chat_id=chat_id)
    ans = {
        "text": "loading"
    }
    return ans