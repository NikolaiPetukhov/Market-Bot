import logging
import json
import importlib
import telegram

from django.views.generic import View
from django.http.response import JsonResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from telegram import Message, CallbackQuery

from .models import BotUser, Bot, TemporaryDataStorage, Shop, Product, ShopAPIKey
from .serializers import ProductSerializer
from . import (
    AdminBotCommands,
    AdminBotCallbackCommands,
    ShopBotCommands,
    ShopBotCallbackCommands,
)
from .permissions import HasShopAPIKey


ADMIN_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
telegram_bot = telegram.Bot(ADMIN_BOT_TOKEN)
logger = logging.getLogger(__name__)

admin_bot_commands = {
    "unknown": AdminBotCommands.unknown,
    "new_shop": AdminBotCommands.new_shop,
    "my_shops": AdminBotCommands.my_shops,
    "change_bot_token_confirm": AdminBotCommands.change_bot_token_confirm,
}

admin_bot_callback_commands = {
    "unknown": AdminBotCallbackCommands.unknown,
    "new_shop_abort": AdminBotCallbackCommands.new_shop_abort,
    "new_shop_confirm": AdminBotCallbackCommands.new_shop_confirm,
    "shop_menu": AdminBotCallbackCommands.shop_menu,
    "delete_shop": AdminBotCallbackCommands.delete_shop,
    "new_api_key": AdminBotCallbackCommands.new_api_key,
    "new_api_key_confirm": AdminBotCallbackCommands.new_api_key_confirm,
    "new_api_key_abort": AdminBotCallbackCommands.new_api_key_abort,
    "change_bot_token": AdminBotCallbackCommands.change_bot_token,
    "delete_shop_confirm": AdminBotCallbackCommands.delete_shop_confirm,
    "delete_shop_abort": AdminBotCallbackCommands.delete_shop_abort,
    "change_name": AdminBotCallbackCommands.change_shop_name,
}

shop_bot_commands = {
    "unknown": ShopBotCommands.unknown,
    "start": ShopBotCommands.start,
    "🏠Main Menu": ShopBotCommands.main_menu,
    "menu": ShopBotCommands.main_menu,
}

shop_bot_callback_commands = {"unknown": ShopBotCallbackCommands.unknown}


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
        if command_name[0] == "/":
            command_name = command_name[1:]
    except:
        command_name = "unknown"
    try:
        args = message_text.split()[1:]
    except:
        args = []
    func = commands.get(command_name, commands["unknown"])
    return func, args


def get_waiting_input_from_user(bot_user):
    try:
        function_name = TemporaryDataStorage.get_functions_waiting_input(bot_user)
        module_name = "." + function_name.split(".")[0]
        function_name = function_name.split(".")[1]
    except:
        return False, None
    try:
        module = importlib.import_module(module_name, "TelegramBot")
    except Exception as e:
        logger.error('Module not found. ' + str(e))
        return False, None
    try:
        func = getattr(module, function_name)
    except Exception as e:
        logger.error('Function not found. ' + str(e))
        return False, None
    return True, func


class CommandReceiveView(View):

    def __handle_message(self, message, telegram_bot, commands):
        bot_user, _ = BotUser.get_or_create_from_chat(message.chat)
        kwargs = {
            "telegram_bot": telegram_bot,
            "bot_user": bot_user,
            "chat_id": message.chat_id,
            "message_id": message.message_id
        }
        shop = Shop.get_shop_by_token(telegram_bot.token)
        if shop:
            shop.add_client(bot_user)
            kwargs["shop"] = shop

        message_text = message.text
        logger.info(f"Private message. Text: {message_text}, Chat_id: {message.chat_id}")

        waiting_input, func = get_waiting_input_from_user(bot_user)
        if waiting_input:
            kwargs["user_input"] = message_text
            func(**kwargs)
            return
        func, args = get_command(commands, message_text)
        func(*args, **kwargs)
    
    def __handle_callback(self, callback_query, telegram_bot, callback_commands):
        bot_user = BotUser.get_by_chat_id(callback_query.from_user.id)
        callback_data = json.loads(callback_query.data)
        func, kwargs = get_callback_command(callback_commands, callback_data)
        kwargs["telegram_bot"] = telegram_bot
        kwargs["bot_user"] = bot_user
        kwargs["chat_id"] = callback_query.message.chat_id
        kwargs["message_id"] = callback_query.message.message_id
        shop = Shop.get_shop_by_token(telegram_bot.token)
        if shop:
            kwargs["shop"] = shop
        
        logger.info(f"Callback Command. Data: {callback_data}, Chat_id: {callback_query.from_user.id}")
        
        answer = func(**kwargs)
        answer["callback_query_id"] = callback_query.id
        try:
            telegram_bot.answer_callback_query(**answer)
        except:
            pass

    def post(self, request, bot_token):
        #
        if bot_token == ADMIN_BOT_TOKEN:
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
                logger.info(f"Invalid token. Token: {bot_token}")
                HttpResponseForbidden("Invalid token")

        raw = request.body.decode("utf-8")
        data = json.loads(raw)

        callback_query_data = data.get("callback_query", False)
        if callback_query_data:
            callback_query = CallbackQuery.de_json(callback_query_data, telegram_bot)
            self.__handle_callback(callback_query, telegram_bot, callback_commands)
            return JsonResponse({}, status=200)

        message_data = data.get("message", False)
        if message_data:
            message = Message.de_json(message_data, telegram_bot)
            chat = message.chat
            if chat.type == "private":
                self.__handle_message(message, telegram_bot, commands)
                return JsonResponse({}, status=200)

        return JsonResponse({}, status=200)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CommandReceiveView, self).dispatch(request, *args, **kwargs)


@api_view(["GET"])
def apiInfoView(request):
    api_urls = {
        "Get list of products": "GET api/products",
        "Create new product": "POST api/products",
        "Get product": "GET api/product/<id>",
        "Update product": "PUT or PATCH api/product/<id>",
    }
    return Response(data=api_urls)


class ProductsApiView(APIView):
    permission_classes = [HasShopAPIKey]

    def get(self, request):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ShopAPIKey.objects.get_from_key(key)
        try:
            shop = Shop.objects.get(api_key=api_key)
        except:
            # shop not found by apikey
            return Response(
                data={"error_message": "Shop not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        products = Product.objects.filter(shop=shop)
        serializer = ProductSerializer(products, many=True)
        return Response(data=serializer.data)

    def post(self, request):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ShopAPIKey.objects.get_from_key(key)
        try:
            shop = Shop.objects.get(api_key=api_key)
        except:
            # shop not found by apikey
            return Response(
                data={"error_message": "Shop not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(shop=shop)
        return Response(data=serializer.data)


class ProductApiView(APIView):
    permission_classes = [HasShopAPIKey]

    def get(self, request, id):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ShopAPIKey.objects.get_from_key(key)
        try:
            _ = Shop.objects.get(api_key=api_key)
        except:
            # shop not found by apikey
            return Response(
                data={"error_message": "Shop not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            product = Product.objects.get(pk=id)
        except:
            # product not found by id
            return Response(
                data={"error_message": "Product not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ProductSerializer(product, many=False)
        return Response(data=serializer.data)

    def put(self, request, id):
        return self.patch(request, id)

    def patch(self, request, id):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ShopAPIKey.objects.get_from_key(key)
        try:
            shop = Shop.objects.get(api_key=api_key)
        except:
            # shop not found by apikey
            return Response(
                data={"error_message": "Wrong API-Key"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            product = Product.objects.get(pk=id)
        except:
            # product not found by id
            return Response(
                data={"error_message": "Product not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if product.shop != shop:
            return Response(
                data={"error_message": "Product not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ProductSerializer(
            product, data=request.data, many=False, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
