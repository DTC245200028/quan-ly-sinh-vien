from django.contrib import admin
from django.http import JsonResponse
from django.db import DatabaseError, connection
from django.urls import path
from django.views.decorators.http import require_safe
from django.views.generic import RedirectView


@require_safe
def healthz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("healthz", healthz, name="healthz"),
]
