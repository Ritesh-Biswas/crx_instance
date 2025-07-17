from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
import logging
from django.http import HttpResponseForbidden 

class LoginRequiredMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_prefixes = [
            reverse('account_login'),
            reverse('account_logout'),
            '/accounts/',
            '/components/',
            '/docs/',
            '/search/',
            '/up/',
            '/media/',
        ]

    def __call__(self, request):
        #check if django-admin
        # if request.path.startswith('/django-admin/'):
        #     print(request.user.groups.all().filter(name='Tenant Group').exists())
        #     print(request.user.is_superuser)
        #     # if not request.user.is_authenticated:
        #     #     return redirect('account_login')
        #     if not (request.user.is_superuser  or request.user.groups.filter(name='Tenant Group').exists()):
        #         return HttpResponseForbidden('Access denied')
        #     if request.user.groups.filter(name='Tenant Group').exists():
        #         return self.get_response(request)
            
        if request.user.is_authenticated:
            return self.get_response(request)

        if any(request.path.startswith(prefix) for prefix in self.allowed_prefixes):
            return self.get_response(request)

        return redirect('account_login')
