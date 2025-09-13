
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # django-autocomplete-light URL даректерин кошуу
    path('', include('core.urls')),  # core тиркемесинин URL даректерин кошуу
]
