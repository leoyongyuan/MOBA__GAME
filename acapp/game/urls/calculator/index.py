from django.urls import path, re_path
from game.views.calculator.index import index


urlpatterns = [
    re_path(r".*", index, name="calculator_index"),
]

