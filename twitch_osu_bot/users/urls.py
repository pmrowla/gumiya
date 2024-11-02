from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path("~redirect/", view=views.UserRedirectView.as_view(), name="redirect"),
    path("", view=views.UserDetailView.as_view(), name="detail"),
    path(
        "~osu-account/",
        view=views.OsuUsernameView.as_view(),
        name="osu-account",
    ),
]
