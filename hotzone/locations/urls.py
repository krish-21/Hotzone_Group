from django.urls import path

from locations import views
from .views import HomePage, get_name, save_address, list_locations

urlpatterns = [
    path('',
        HomePage.as_view(),
        name='index'),
    path('search',
        get_name,
        name='search'),
    path('save',
        save_address,
        name='save'),
    path('list',
        list_locations,
        name='list')
]