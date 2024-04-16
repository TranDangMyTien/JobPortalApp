import debug_toolbar
from django.contrib import admin
from django.urls import path
from django.urls import path, include, re_path
from jobPortal import settings
from jobs.admin import my_admin_site

urlpatterns = [
    path('', include('jobs.urls')),
    path('admin/', admin.site.urls),
    # path('myadmin/', my_admin_site.urls),
    path('__debug__/', include(debug_toolbar.urls)),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns += [
    path('myadmin/', my_admin_site.urls),
]