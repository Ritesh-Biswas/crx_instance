from coderedcms import admin_urls as crx_admin_urls
from coderedcms import search_urls as crx_search_urls
from coderedcms import urls as crx_urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from wagtail.documents import urls as wagtaildocs_urls
from website.views import LoginView, LogoutView
from django.http import HttpResponse

def health_check(request):
    return HttpResponse(status=200)

urlpatterns = [
    # Admin
    path("myadmin/", admin.site.urls),
    path("admin/", include(crx_admin_urls)),
    # Documents
    path("docs/", include(wagtaildocs_urls)),
    # Search
    path("search/", include(crx_search_urls)),
    # Allauth
    path('accounts/login/', LoginView.as_view(), name='account_login'),
    path('accounts/logout/', LogoutView.as_view(), name='account_logout'),
    path('accounts/', include('allauth.urls')),
    # For anything not caught by a more specific rule above, hand over to
    # the page serving mechanism. This should be the last pattern in
    # the list:
    path("components/", include("components.urls", namespace="components")),
    path('custom_user/', include('custom_user.urls')),
    path('comment/', include('comment.urls')),
    path("up/", health_check),
    path('', include('home.urls')),
    path("", include(crx_urls)),
    # Alternatively, if you want pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(crx_urls)),
]


# fmt: off
if settings.DEBUG:
    from django.conf.urls.static import static

    # Serve static and media files from development server
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # type: ignore
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # type: ignore
# fmt: on


from django.contrib import admin
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp, EmailAddress
from comment.models import Follower

admin.site.unregister(Follower)

# Base admin mixin for tenant restrictions
class TenantRestrictedAdminMixin:
    def has_module_permission(self, request):
        if request.user.groups.filter(name="Tenant").exists():
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.groups.filter(name="Tenant").exists():
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name="Tenant").exists():
            return False
        return super().has_change_permission(request, obj)

class CustomEmailAddressAdmin(TenantRestrictedAdminMixin, admin.ModelAdmin):
    pass

class CustomSocialAppAdmin(TenantRestrictedAdminMixin, admin.ModelAdmin):
    pass

# Unregister default and register custom admins
admin.site.unregister(EmailAddress)
admin.site.register(EmailAddress, CustomEmailAddressAdmin)

admin.site.unregister(SocialApp)
admin.site.register(SocialApp, CustomSocialAppAdmin)
