import telegram

from django.db import transaction
from django.conf import settings

from .error import SetWebhookError
from .models import Shop, Bot


@transaction.atomic
def create_new_shop(data, bot_user):
    name = data["name"]
    token = data["token"]
    bot = telegram.Bot(token)
    info = bot.get_me()
    try:
        my_url = settings.PROJECT_URL
        bot.set_webhook(f"{my_url}/{token}")
    except:
        raise SetWebhookError
    shop_obj = Shop.create(name=name, owner=bot_user)
    bot_obj = Bot.create(
        token=token, shop=shop_obj, username=info.username, name=info.first_name
    )
    shop_obj.save()
    bot_obj.save()
