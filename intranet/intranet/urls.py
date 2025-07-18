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
