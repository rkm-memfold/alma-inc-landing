from django.contrib import admin
from django.urls import path

from waitlist.views import healthz, join_waitlist

urlpatterns = [
    path("admin/", admin.site.urls),
    path("waitlist", join_waitlist),
    path("healthz", healthz),
]
