from rest_framework_api_key.permissions import BaseHasAPIKey
from .models import ShopAPIKey

class HasShopAPIKey(BaseHasAPIKey):
    model = ShopAPIKey