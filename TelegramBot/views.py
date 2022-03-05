import logging, json, importlib
from tempfile import TemporaryFile

from django.views.generic import View
from django.http.response import JsonResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import telegram
from telegram import Message, CallbackQuery

from .models import BotUser, Bot, TemporaryDataStorage
from . import AdminBotCommands, AdminBotCallbackCommands, ShopBotCommands, ShopBotCallbackCommands

admin_bot_token = settings.TELEGRAM_BOT_TOKEN
telegram_bot = telegram.Bot(admin_bot_token)
logger = logging.getLogger("telegram.bot")

admin_bot_commands = {
    "unknown": AdminBotCommands.unknown,
    "new_shop": AdminBotCommands.new_shop,
    "cancel": AdminBotCommands.new_shop_abort
}

admin_bot_callback_commands = {
    "unknown": AdminBotCallbackCommands.unknown,
    "new_shop_abort": AdminBotCallbackCommands.new_shop_abort,
    "new_shop_confirm": AdminBotCallbackCommands.new_shop_confirm
}

shop_bot_commands = {
    "unknown": ShopBotCommands.unknown
}

shop_bot_callback_commands = {
    "unknown": ShopBotCallbackCommands.unknown
}


def find_bot(token):
    return Bot.objects.get(token=token)


def get_callback_command(callback_commands, callback_data):
    comm = callback_data.get("comm", "unknown")
    func = callback_commands.get(comm, callback_commands["unknown"])
    kwargs = callback_data.get("args", {})
    return func, kwargs


def get_command(commands, message_text):
    try:
        command_name = message_text.split()[0].lower()
        if command_name[0] == '/': command_name = command_name[1:]
    except:
        command_name = "unknown"
    try:
        args = message_text.split()[1:]
    except:
        args = []
    func = commands.get(command_name, commands["unknown"])
    return func, args

# data = {
#   "user_data": {
#      "new_product": {
#           "message_id": <Int>,  -- id of message which will be edited
#           "name": <String>,
#           "description": <String>,
#           "price": <Decimal>,
#           "tags": <String>,
#       },
#       "new_shop": {
#           "message_id": <int>, -- id of message which will be edited
#           "name": <String>,
#           "token": <String>,
#       },
#       "active_shop": id <int> -- id of the shop
#   },
#   "functions_waiting_input": {
#       "bot_user_id": "function_name"
#   }
# }
def get_waiting_input_from_user(bot_user):
    data = TemporaryDataStorage.get_data()
    try:
        function_name = data["functions_waiting_input"][str(bot_user.id)]
    except:
        return False, None
    module_name = '.'+function_name.split('.')[0]
    function_name = function_name.split('.')[1]
    try:
        module = importlib.import_module(module_name, 'TelegramBot')
    except Exception as e:
        print('module not found')
        print(e)
        return False, None
    try:
        func = getattr(module, function_name)
    except Exception as e:
        print('function not found')
        print(e)
        return False, None
    return True, func


class CommandReceiveView(View):
    def post(self, request, bot_token):
        # 
        if bot_token == admin_bot_token:
            telegram_bot = telegram.Bot(bot_token)
            commands = admin_bot_commands
            callback_commands = admin_bot_callback_commands
        else:
            bot_obj = find_bot(bot_token)
            if bot_obj:
                telegram_bot = telegram.Bot(bot_token)
                commands = shop_bot_commands
                callback_commands = shop_bot_callback_commands
            else:
                print("Invalid token")
                HttpResponseForbidden("Invalid token")

        raw = request.body.decode("utf-8")
        logger.info(raw)
        data = json.loads(raw)

        is_edit_message = data.get("edited_message", False)
        is_callback_query = data.get("callback_query", False)
        
        if is_edit_message:
            pass
        elif is_callback_query:
            callback_query = CallbackQuery.de_json(data["callback_query"], telegram_bot)
            bot_user = BotUser.get_by_chat_id(callback_query.from_user.id)
            callback_data = json.loads(callback_query.data)
            print(callback_data)

            func, kwargs = get_callback_command(callback_commands, callback_data)
            kwargs["telegram_bot"] = telegram_bot
            kwargs["bot_user"] = bot_user
            kwargs["chat_id"] = callback_query.message.chat_id
            kwargs["message_id"] = callback_query.message.message_id
            
            answer = func(**kwargs)

            answer["callback_query_id"] = callback_query.id
            try: 
                telegram_bot.answer_callback_query(
                **answer
            )
            except:
                pass
        else:
            message = Message.de_json(data["message"], telegram_bot)
            bot_user, created = BotUser.get_or_create_from_chat(message.chat)
            message_text = message.text
            print(message_text)

            waiting_input, func = get_waiting_input_from_user(bot_user)
            if waiting_input:
                kwargs = {}
                kwargs["telegram_bot"] = telegram_bot
                kwargs["bot_user"] = bot_user
                kwargs["chat_id"] = message.chat_id
                kwargs["message_id"] = message.message_id
                kwargs["user_input"] = message_text
                func(**kwargs)
                return JsonResponse({}, status=200)

            func, args = get_command(commands, message_text)
            kwargs = {}
            kwargs["telegram_bot"] = telegram_bot
            kwargs["bot_user"] = bot_user
            kwargs["chat_id"] = message.chat_id
            kwargs["message_id"] = message.message_id

            func(*args, **kwargs)
        return JsonResponse({}, status=200)

    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CommandReceiveView, self).dispatch(request, *args, **kwargs)
