from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^~settings/$',
        view=views.BotOptionsView.as_view(),
        name='settings'),
]
