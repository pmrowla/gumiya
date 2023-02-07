from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, RedirectView
from django.views.generic.edit import FormView

from ..streams.models import BotOptions, TwitchUser
from . import signals
from .forms import SetOsuUsernameForm
from .models import OsuUsername, User


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User

    def get_object(self):
        # Only get the User record for the user making the request
        user = User.objects.get(username=self.request.user.username)
        try:
            twitch_user = TwitchUser.objects.get(user=user)
        except ObjectDoesNotExist:
            twitch_user = TwitchUser.update_or_create(user)
        BotOptions.objects.get_or_create(twitch_user=twitch_user)
        return user


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        try:
            user = User.objects.get(username=self.request.user.username)
            TwitchUser.update_or_create(user)
        except ObjectDoesNotExist:
            pass
        return reverse("users:detail")


class OsuUsernameView(LoginRequiredMixin, FormView):
    model = OsuUsername
    template_name = "users/osu_username_form.html"
    form_class = SetOsuUsernameForm

    def get_success_url(self):
        return reverse("users:detail")

    def form_valid(self, form):
        form.save(self.request)
        return super(OsuUsernameView, self).form_valid(form)

    def post(self, request, *args, **kwargs):
        res = None
        if "action_set" in request.POST:
            res = super(OsuUsernameView, self).post(request, *args, **kwargs)
        elif request.POST.get("username"):
            if "action_verify" in request.POST:
                res = self._action_verify(request)
            elif "action_unlink" in request.POST:
                res = self._action_unlink(request)
            res = res or HttpResponseRedirect(self.get_success_url())
        else:
            res = HttpResponseRedirect(self.get_success_url())
        return res

    def _action_verify(self, request, *args, **kwargs):
        username = request.POST.get("username")
        try:
            osu_username = OsuUsername.objects.get(user=request.user, username=username)
            osu_username.send_confirmation(request, message=True)
            return HttpResponseRedirect(self.get_success_url())
        except OsuUsername.DoesNotExist:
            pass

    def _action_unlink(self, request, *args, **kwargs):
        username = request.POST.get("username")
        try:
            osu_username = OsuUsername.objects.get(user=request.user)
            osu_username.delete()
            signals.osu_username_unlinked.send(
                sender=request.user.__class__,
                request=request,
                user=request.user,
                username=username,
            )
            messages.success(request, "Successfully unlinked your Osu! account.")
            return HttpResponseRedirect(self.get_success_url())
        except OsuUsername.DoesNotExist:
            pass
