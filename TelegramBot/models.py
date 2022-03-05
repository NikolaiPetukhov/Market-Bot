from decimal import Decimal
from unicodedata import category
from django.db import models


class BotUser(models.Model):
    username = models.CharField(verbose_name="Username", max_length=1024, blank=True, null=True)
    first_name = models.CharField(verbose_name="Name", max_length=1024, blank=True, null=True)
    last_name = models.CharField(verbose_name="Surname", max_length=1024, blank=True, null=True)
    chat_id = models.IntegerField(verbose_name="Id of a chat", unique=True)
    is_admin = models.BooleanField(verbose_name="Admin", default=False)


    def __str__(self):
        return f"{self.username}"

    @staticmethod
    def get_or_create_from_chat(chat):
        obj, created = BotUser.objects.get_or_create(
            chat_id=chat.id
        )
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
    owner = models.ForeignKey(BotUser, related_name='owner', null=True, on_delete=models.SET_NULL)
    clients = models.ManyToManyField(BotUser, related_name='clients')

class Bot(models.Model):
    token = models.CharField(max_length=69, unique=True)
    username = models.CharField(max_length=69, null=True, blank=True)
    name = models.CharField(max_length=69, null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

class Category(models.Model):
    name = models.CharField(max_length=69)
    parent = models.ForeignKey('Category', null=True, on_delete=models.SET_NULL)

class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    name = models.CharField(max_length=69)
    price = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0.0'))
    description = models.TextField(max_length=1024, null=True, blank=True)
    tags = models.CharField(max_length=1024, null=True, blank=True)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)


# To be changed in future 
class TemporaryDataStorage(models.Model):
    data = models.JSONField(null=True)

    @classmethod
    def get_data(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj.data if obj.data else {}

    @classmethod
    def put_data(cls, data):
        obj, _ = cls.objects.get_or_create(pk=1)
        obj.data = data
        obj.save()
    

    

