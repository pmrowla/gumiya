from django.urls import path

from . import views

app_name = "streams"
urlpatterns = [
    path("~settings/", view=views.BotOptionsView.as_view(), name="settings"),
]
