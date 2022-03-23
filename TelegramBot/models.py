from decimal import Decimal
from django.db import models
from rest_framework_api_key.models import AbstractAPIKey


class BotUser(models.Model):
    username = models.CharField(
        verbose_name="Username", max_length=1024, blank=True, null=True
    )
    first_name = models.CharField(
        verbose_name="Name", max_length=1024, blank=True, null=True
    )
    last_name = models.CharField(
        verbose_name="Surname", max_length=1024, blank=True, null=True
    )
    chat_id = models.IntegerField(verbose_name="Id of a chat", unique=True)
    is_admin = models.BooleanField(verbose_name="Admin", default=False)
    max_shops = models.IntegerField(default=2)

    def __str__(self):
        return f"{self.username}"

    @staticmethod
    def get_or_create_from_chat(chat):
        obj, created = BotUser.objects.get_or_create(chat_id=chat.id)
        obj.username = chat.username
        obj.last_name = chat.last_name
        obj.first_name = chat.first_name
        obj.save()
        return obj, created

    @staticmethod
    def get_by_chat_id(chat_id):
        try:
            obj = BotUser.objects.get(chat_id=chat_id)
        except:
            obj = None
        return obj


class Shop(models.Model):
    name = models.CharField(max_length=69)
    owner = models.ForeignKey(
        BotUser, related_name="owner", null=True, on_delete=models.SET_NULL
    )
    clients = models.ManyToManyField(BotUser, related_name="clients")
    welcome_message = models.TextField(max_length=256, null=True, blank=True)

    @classmethod
    def create(cls, name, owner):
        shop = cls(name=name, owner=owner)
        return shop

    def revoke_api_key(self):
        try:
            api_key = ShopAPIKey.objects.get(shop=self)
            api_key.delete()
        except:
            pass
        api_key, key = ShopAPIKey.objects.create_key(
            shop=self, name=f"Shop({self.pk})_apikey"
        )
        return api_key, key

    @classmethod
    def get_shop_by_token(cls, token):
        try:
            bot = Bot.objects.get(token=token)
            return bot.shop
        except:
            return None

    def add_client(self, client):
        self.clients.add(client)
        self.save()

    @classmethod
    def create(cls, name, owner):
        shop = cls(name=name, owner=owner)
        return shop

    def revoke_api_key(self):
        try:
            api_key = ShopAPIKey.objects.get(shop=self)
            api_key.delete()
        except:
            pass
        api_key, key = ShopAPIKey.objects.create_key(
            shop=self, name=f"Shop({self.pk})_apikey"
        )
        return api_key, key


class Bot(models.Model):
    token = models.CharField(max_length=69, unique=True, primary_key=False)
    username = models.CharField(max_length=69, null=True, blank=True)
    name = models.CharField(max_length=69, null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    @classmethod
    def create(cls, token, shop, name=None, username=None):
        obj = cls(token=token, shop=shop, name=name, username=username)
        return obj


class Category(models.Model):
    name = models.CharField(max_length=69)
    parent = models.ForeignKey("Category", null=True, on_delete=models.SET_NULL)


class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    name = models.CharField(max_length=69)
    price = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal("0.0"))
    description = models.TextField(max_length=1024, null=True, blank=True)
    tags = models.CharField(max_length=1024, null=True, blank=True)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)


class ShopAPIKey(AbstractAPIKey):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="api_key",
    )


# To be changed in future
class TemporaryDataStorage(models.Model):
    """
    data = {
        ### Admin Bot Related Fields ###
        'function_waiting_input': function name (str),
        'new_product': {
            'message_id': message_id (int) -- id of message with new product info.
            'name': product_name (str)
            'description': product_description (str)
            'price' product price (Decimal)
        },
        'new_shop': {
            'message_id': message_id (int) -- id of message with new shop info
            'name': name (str)
            'token' (str) -- bot token
        }
        'new_token_shop_id': shop_id (id)

        ### Shop Bot Related Fields ###
        'cart': {
            items: [
                {
                    'id': item_id(int),
                    'quantity': quantity(int),
                },
                ...
            ]
        }
    }
    """

    bot_user = models.ForeignKey(BotUser, on_delete=models.CASCADE)
    data = models.JSONField(null=True, default=dict)

    @classmethod
    def get_data(cls, bot_user):
        obj, _ = cls.objects.get_or_create(bot_user=bot_user)
        return obj.data if obj.data else {}

    @classmethod
    def put_data(cls, bot_user, data):
        obj, _ = cls.objects.get_or_create(bot_user=bot_user)
        obj.data = data
        obj.save()

    @classmethod
    def put_field_value(cls, bot_user, fieldname, value):
        obj, _ = cls.objects.get_or_create(bot_user=bot_user)
        data = obj.data
        data[fieldname] = value
        obj.data = data
        obj.save()

    @classmethod
    def get_field_value(cls, bot_user, fieldname):
        obj, _ = cls.objects.get_or_create(bot_user=bot_user)
        data = obj.data
        return data.get(fieldname, None)

    @classmethod
    def delete_field(cls, bot_user, fieldname):
        obj, _ = cls.objects.get_or_create(bot_user=bot_user)
        data = obj.data
        data.pop(fieldname, None)
        obj.data = data
        obj.save()

    @classmethod
    def put_function_waiting_input(cls, bot_user, function_name):
        cls.put_field_value(bot_user, "function_waiting_input", function_name)

    @classmethod
    def get_functions_waiting_input(cls, bot_user):
        return cls.get_field_value(bot_user, "function_waiting_input")

    @classmethod
    def delete_function_waiting_input(cls, bot_user):
        cls.delete_field(bot_user, "function_waiting_input")

    @classmethod
    def put_new_shop_data(cls, bot_user, field_name, field_value):
        try:
            obj, _ = cls.objects.get_or_create(bot_user=bot_user)
            data = obj.data
            if "new_shop" not in data.keys():
                data["new_shop"] = {}
            data["new_shop"][field_name] = str(field_value)
            obj.data = data
            obj.save()
            return True
        except:
            return False

    @classmethod
    def get_new_shop_data(cls, bot_user):
        return cls.get_field_value(bot_user, "new_shop")

    @classmethod
    def delete_new_shop_data(cls, bot_user):
        cls.delete_field(bot_user, "new_shop")

    @classmethod
    def put_new_token_shop_id(cls, bot_user, shop_id):
        cls.put_field_value(bot_user, "new_token_shop_id", shop_id)

    @classmethod
    def get_new_token_shop_id(cls, bot_user):
        return cls.get_field_value(bot_user, "new_token_shop_id")

    @classmethod
    def delete_new_token_shop_id(cls, bot_user):
        cls.delete_field(bot_user, "new_token_shop_id")

    @classmethod
    def put_new_name_shop_id(cls, bot_user, shop_id):
        cls.put_field_value(bot_user, "new_name_shop_id", shop_id)

    @classmethod
    def get_new_name_shop_id(cls, bot_user):
        return cls.get_field_value(bot_user, "new_name_shop_id")

    @classmethod
    def delete_new_name_shop_id(cls, bot_user):
        cls.delete_field(bot_user, "new_name_shop_id")
