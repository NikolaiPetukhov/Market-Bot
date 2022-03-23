from django.urls import path

from .views import apiInfoView, ProductsApiView, ProductApiView


urlpatterns = [
    path("", apiInfoView, name="API Info"),
    path("products", ProductsApiView.as_view(), name="Products"),
    path("product/<int:id>", ProductApiView.as_view(), name="Product"),
]
