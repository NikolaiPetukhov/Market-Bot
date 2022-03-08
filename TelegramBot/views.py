import logging, json, importlib

from django.views.generic import View
from django.http.response import JsonResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view

import telegram
from telegram import Message, CallbackQuery

from .models import BotUser, Bot, TemporaryDataStorage, Shop, Product, ShopAPIKey
from .serializers import ProductSerializer
from . import AdminBotCommands, AdminBotCallbackCommands, ShopBotCommands, ShopBotCallbackCommands
from .permissions import HasShopAPIKey
from TelegramBot import serializers

admin_bot_token = settings.TELEGRAM_BOT_TOKEN
telegram_bot = telegram.Bot(admin_bot_token)
logger = logging.getLogger("telegram.bot")

admin_bot_commands = {
    "unknown": AdminBotCommands.unknown,
    "new_shop": AdminBotCommands.new_shop,
    "cancel": AdminBotCommands.new_shop_abort,
    "my_shops": AdminBotCommands.my_shops
}

admin_bot_callback_commands = {
    "unknown": AdminBotCallbackCommands.unknown,
    "new_shop_abort": AdminBotCallbackCommands.new_shop_abort,
    "new_shop_confirm": AdminBotCallbackCommands.new_shop_confirm,
    "shop_menu": AdminBotCallbackCommands.shop_menu,
    "delete_shop": AdminBotCallbackCommands.delete_shop,
    "new_api_key": AdminBotCallbackCommands.new_api_key,
    "new_api_key_confirm": AdminBotCallbackCommands.new_api_key_confirm,
    "new_api_key_abort": AdminBotCallbackCommands.new_api_key_abort
}

shop_bot_commands = {
    "unknown": ShopBotCommands.unknown,
    "start": ShopBotCommands.start
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


@api_view(['GET'])
def apiInfoView(request):
    api_urls = {
        'Get list of products': 'GET api/products'
    }
    return Response(data=api_urls)

class ProductsApiView(APIView):
    permission_classes = [HasShopAPIKey]

    def get(self, request):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ShopAPIKey.objects.get_from_key(key)
        try: shop = Shop.objects.get(api_key=api_key)
        except: 
            # shop not found by apikey  
            return Response(data={"error_message":"Shop not found"}, status=status.HTTP_400_BAD_REQUEST) 
        products = Product.objects.filter(shop=shop)
        serializer = ProductSerializer(products, many=True)
        return Response(data=serializer.data)

    def post(self, request):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ShopAPIKey.objects.get_from_key(key)
        try: shop = Shop.objects.get(api_key=api_key)
        except: 
            # shop not found by apikey
            return Response(data={"error_message":"Shop not found"}, status=status.HTTP_400_BAD_REQUEST) 
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid(): serializer.save(shop=shop)
        return Response(data=serializer.data)

class ProductApiView(APIView):
    permission_classes = [HasShopAPIKey]

    def get(self, request, id):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ShopAPIKey.objects.get_from_key(key)
        try: shop = Shop.objects.get(api_key=api_key)
        except: 
            # shop not found by apikey  
            return Response(data={"error_message":"Shop not found"}, status=status.HTTP_400_BAD_REQUEST)
        try: product = Product.objects.get(pk=id)
        except:
            # product not found by id
            return Response(data={"error_message":"Product not found"}, status=status.HTTP_400_BAD_REQUEST) 
        serializer = ProductSerializer(product, many=False)
        return Response(data=serializer.data)

    def put(self, request, id):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ShopAPIKey.objects.get_from_key(key)
        try: shop = Shop.objects.get(api_key=api_key)
        except: 
            # shop not found by apikey  
            return Response(data={"error_message":"Shop not found"}, status=status.HTTP_400_BAD_REQUEST)
        try: product = Product.objects.get(pk=id)
        except:
            # product not found by id
            return Response(data={"error_message":"Product not found"}, status=status.HTTP_400_BAD_REQUEST)
        if product.shop != shop:
            return Response(data={"error_message":"Product not found"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProductSerializer(instance=product, data=request.data)
        if serializer.is_valid(): serializer.save()
        return Response(serializer.data)