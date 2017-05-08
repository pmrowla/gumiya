from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^~redirect/$',
        view=views.UserRedirectView.as_view(),
        name='redirect'
    ),
    url(
        regex=r'^$',
        view=views.UserDetailView.as_view(),
        name='detail'
    ),
    url(
        regex=r'^~osu-account/$',
        view=views.OsuUsernameView.as_view(),
        name='osu-account'),
]
