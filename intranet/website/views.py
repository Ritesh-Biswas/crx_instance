from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import FormView, View
from allauth.socialaccount.models import SocialApp
from wagtail.models import Site
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
import logging

class LoginView(FormView):
    template_name = "account/login.html"
    form_class = AuthenticationForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            wagtail_home = Site.find_for_request(self.request).root_page.url
            return redirect(wagtail_home)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_social_app_exists'] = SocialApp.objects.filter(provider='google').exists()
        context['microsoft_social_app_exists'] = SocialApp.objects.filter(provider='microsoft').exists()            
        return context

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{error}")
        return super().form_invalid(form)

    def form_valid(self, form):
        try:
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(self.request, "This account is inactive.")
                    return self.form_invalid(form)
                login(self.request, user)
                wagtail_home = Site.find_for_request(self.request).root_page.url
                return redirect(wagtail_home)
            else:
                messages.error(
                    self.request,
                    "The username or password you entered is incorrect. Please try again."
                )
                return self.form_invalid(form)
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            messages.error(self.request, "An error occurred during login. Please try again.")
            return self.form_invalid(form)

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("account_login")

    def post(self, request):
        logout(request)
        return redirect("account_login")
