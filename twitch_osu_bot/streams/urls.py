from django.conf.urls import url

from . import views

app_name = 'streams'
urlpatterns = [
    url(
        regex=r'^~settings/$',
        view=views.BotOptionsView.as_view(),
        name='settings'),
]
