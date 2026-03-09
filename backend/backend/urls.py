from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def home(request):
    return JsonResponse({"status": "Employee Directory API running"})


urlpatterns = [
    path('', home),                    
    path('admin/', admin.site.urls),
    path('api/', include('hackathon.urls')),
]